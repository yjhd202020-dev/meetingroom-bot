"""
Business logic for meeting room reservations.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
from models.database import Database

# Weekday names in Korean - shared constant to avoid duplication
WEEKDAY_NAMES_KR = ['월', '화', '수', '목', '금', '토', '일']


def get_weekday_kr(dt: datetime) -> str:
    """Get Korean weekday name from datetime."""
    return WEEKDAY_NAMES_KR[dt.weekday()]


def parse_datetime(dt: Union[str, datetime]) -> datetime:
    """Parse datetime from string if needed."""
    if isinstance(dt, str):
        return datetime.fromisoformat(dt)
    return dt


class ReservationService:
    """Service layer for reservation operations."""

    def __init__(self, db: Database):
        self.db = db

    def create_reservation(
        self,
        room_name: str,
        slack_user_id: str,
        slack_username: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        Attempt to create a reservation.

        Returns:
            {
                'success': bool,
                'message': str,
                'reservation_id': int (if success),
                'conflict': dict (if failed due to overlap)
            }
        """
        # Get room
        room = self.db.get_room_by_name(room_name)
        if not room:
            return {
                'success': False,
                'message': f"❌ 회의실을 찾을 수 없습니다: {room_name}"
            }

        # Check for conflicts
        conflict = self.db.check_overlap(room['id'], start_time, end_time)
        if conflict:
            return {
                'success': False,
                'message': self._format_conflict_message(room_name, start_time, end_time, conflict),
                'conflict': conflict
            }

        # Create reservation
        reservation_id = self.db.create_reservation(
            room['id'],
            slack_user_id,
            slack_username,
            start_time,
            end_time
        )

        if reservation_id:
            return {
                'success': True,
                'message': self._format_success_message(room_name, start_time, end_time, slack_username),
                'reservation_id': reservation_id
            }
        else:
            return {
                'success': False,
                'message': "❌ 예약 중 오류가 발생했습니다. 다시 시도해주세요."
            }

    def get_weekly_status(self, week_offset: int = 0) -> str:
        """Get formatted weekly reservation status.

        Args:
            week_offset: 0 = this week, 1 = next week, -1 = last week
        """
        # Get start of current week (Monday)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday) + timedelta(weeks=week_offset)

        # Get all reservations for this week
        reservations = self.db.get_weekly_reservations(week_start)

        # Get all rooms
        rooms = self.db.get_all_rooms()

        # Group reservations by room
        reservations_by_room = {room['name']: [] for room in rooms}
        for res in reservations:
            reservations_by_room[res['room_name']].append(res)

        # Format message
        week_end = week_start + timedelta(days=6)
        week_label = {-1: "지난 주", 0: "이번 주", 1: "다음 주"}.get(week_offset, "")
        message = f"📅 {week_label} 회의실 예약 현황 ({week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')})\n\n"

        for room in rooms:
            room_name = room['name']
            room_reservations = reservations_by_room[room_name]

            message += f"🏢 *{room_name}*\n"

            if room_reservations:
                for res in room_reservations:
                    start = parse_datetime(res['start_time'])
                    end = parse_datetime(res['end_time'])

                    message += f"   • {start.strftime('%m/%d')} ({get_weekday_kr(start)}) "
                    message += f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} "
                    message += f"| <@{res['slack_user_id']}>\n"
            else:
                message += "   (예약 없음)\n"

            message += "\n"

        return message.strip()

    def _format_success_message(
        self,
        room_name: str,
        start_time: datetime,
        end_time: datetime,
        username: str
    ) -> str:
        """Format successful reservation message."""
        return f"""✅ *예약 완료!*

🏢 회의실: *{room_name}*
📅 날짜: {start_time.strftime('%Y년 %m월 %d일')} ({get_weekday_kr(start_time)})
🕐 시간: {start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}
👤 예약자: {username}"""

    def _format_conflict_message(
        self,
        room_name: str,
        requested_start: datetime,
        requested_end: datetime,
        conflict: dict
    ) -> str:
        """Format conflict error message."""
        existing_start = parse_datetime(conflict['start_time'])
        existing_end = parse_datetime(conflict['end_time'])

        return f"""❌ *예약 불가*

🏢 회의실: *{room_name}*
🕐 요청 시간: {requested_start.strftime('%m/%d %H:%M')} ~ {requested_end.strftime('%H:%M')}
⚠️ 이유: 해당 시간에 이미 예약이 있습니다.

*기존 예약 정보:*
📅 날짜: {existing_start.strftime('%Y년 %m월 %d일')} ({get_weekday_kr(existing_start)})
🕐 시간: {existing_start.strftime('%H:%M')} ~ {existing_end.strftime('%H:%M')}
👤 예약자: <@{conflict['slack_user_id']}>"""

    def get_user_reservations(self, slack_user_id: str) -> Dict:
        """Get user's upcoming reservations with formatted message."""
        reservations = self.db.get_user_reservations(slack_user_id)

        if not reservations:
            return {
                'success': True,
                'message': "📭 예약된 회의실이 없습니다.",
                'reservations': []
            }

        message = "📋 *내 예약 목록*\n\n"
        for res in reservations:
            start = parse_datetime(res['start_time'])
            end = parse_datetime(res['end_time'])

            message += f"*[{res['id']}]* 🏢 {res['room_name']}\n"
            message += f"   📅 {start.strftime('%m/%d')} ({get_weekday_kr(start)}) {start.strftime('%H:%M')}-{end.strftime('%H:%M')}\n\n"

        message += "_취소하려면: `@봇 [번호] 취소` (예: `@봇 5 취소`)_"

        return {
            'success': True,
            'message': message,
            'reservations': reservations
        }

    def cancel_reservation(self, reservation_id: int, slack_user_id: str) -> Dict:
        """Cancel a reservation by ID."""
        reservation = self.db.get_reservation_by_id(reservation_id)

        if not reservation:
            return {
                'success': False,
                'message': f"❌ 예약 번호 {reservation_id}를 찾을 수 없습니다."
            }

        if reservation['slack_user_id'] != slack_user_id:
            return {
                'success': False,
                'message': "❌ 본인의 예약만 취소할 수 있습니다."
            }

        deleted = self.db.delete_reservation(reservation_id, slack_user_id)

        if deleted:
            start = parse_datetime(reservation['start_time'])
            end = parse_datetime(reservation['end_time'])

            return {
                'success': True,
                'message': f"""✅ *예약이 취소되었습니다*

🏢 회의실: *{reservation['room_name']}*
📅 날짜: {start.strftime('%Y년 %m월 %d일')} ({get_weekday_kr(start)})
🕐 시간: {start.strftime('%H:%M')} ~ {end.strftime('%H:%M')}"""
            }
        return {
            'success': False,
            'message': "❌ 예약 취소 중 오류가 발생했습니다."
        }

    def get_all_reservations(self) -> str:
        """Get all future reservations formatted as message."""
        reservations = self.db.get_all_future_reservations()

        if not reservations:
            return "📭 예약된 회의실이 없습니다."

        message = "📋 *전체 예약 현황*\n\n"

        # Group by date
        by_date: Dict[str, List] = {}
        for res in reservations:
            start = parse_datetime(res['start_time'])
            date_key = start.strftime('%Y-%m-%d')
            if date_key not in by_date:
                by_date[date_key] = []
            by_date[date_key].append(res)

        for date_key in sorted(by_date.keys()):
            date_reservations = by_date[date_key]
            first_start = parse_datetime(date_reservations[0]['start_time'])

            message += f"*📅 {first_start.strftime('%m/%d')} ({get_weekday_kr(first_start)})*\n"

            for res in date_reservations:
                res_start = parse_datetime(res['start_time'])
                res_end = parse_datetime(res['end_time'])
                message += f"   • {res['room_name']} {res_start.strftime('%H:%M')}-{res_end.strftime('%H:%M')} | <@{res['slack_user_id']}>\n"

            message += "\n"

        return message.strip()

    def create_recurring_reservation(
        self,
        room_name: str,
        slack_user_id: str,
        slack_username: str,
        weekday: int,
        start_hour: int,
        start_minute: int,
        end_hour: int,
        end_minute: int,
        weeks: int = 4
    ) -> Dict:
        """Create recurring reservations for N weeks."""
        room = self.db.get_room_by_name(room_name)
        if not room:
            return {
                'success': False,
                'message': f"❌ 회의실을 찾을 수 없습니다: {room_name}"
            }

        created_ids, conflicts = self.db.create_recurring_reservations(
            room_id=room['id'],
            slack_user_id=slack_user_id,
            slack_username=slack_username,
            start_hour=start_hour,
            start_minute=start_minute,
            end_hour=end_hour,
            end_minute=end_minute,
            weekday=weekday,
            weeks=weeks
        )

        if not created_ids:
            return {
                'success': False,
                'message': f"❌ 예약 생성 실패. 모든 날짜에 충돌이 있습니다.\n충돌 날짜: {', '.join(conflicts)}"
            }

        message = f"""✅ *반복 예약 완료!*

🏢 회의실: *{room_name}*
📅 일정: 매주 {WEEKDAY_NAMES_KR[weekday]}요일
🕐 시간: {start_hour:02d}:{start_minute:02d} ~ {end_hour:02d}:{end_minute:02d}
🔁 생성된 예약: {len(created_ids)}건 ({weeks}주간)"""

        if conflicts:
            message += f"\n⚠️ 충돌로 제외된 날짜: {', '.join(conflicts)}"

        return {
            'success': True,
            'message': message,
            'reservation_ids': created_ids
        }
