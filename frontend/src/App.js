import React, { useState, useEffect, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth, addWeeks, addMonths, subWeeks, subMonths } from 'date-fns';
import { ko } from 'date-fns/locale';

const API_BASE = process.env.REACT_APP_API_URL || '';

const ROOMS = [
  { name: 'Delhi', nameKr: '델리', color: { bg: '#e3f2fd', border: '#1976d2', text: '#1565c0' } },
  { name: 'Mumbai', nameKr: '뭄바이', color: { bg: '#fff3e0', border: '#f57c00', text: '#e65100' } },
  { name: 'Chennai', nameKr: '첸나이', color: { bg: '#e8f5e9', border: '#43a047', text: '#2e7d32' } },
];

function App() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState('week'); // 'week' or 'month'
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [tooltip, setTooltip] = useState(null);

  const fetchReservations = useCallback(async () => {
    setLoading(true);
    try {
      let startDate, endDate;

      if (view === 'week') {
        startDate = format(startOfWeek(currentDate, { weekStartsOn: 1 }), 'yyyy-MM-dd');
        endDate = format(endOfWeek(currentDate, { weekStartsOn: 1 }), 'yyyy-MM-dd');
      } else {
        startDate = format(startOfMonth(currentDate), 'yyyy-MM-dd');
        endDate = format(endOfMonth(currentDate), 'yyyy-MM-dd');
      }

      const url = new URL(`${API_BASE}/api/reservations`, window.location.origin);
      url.searchParams.set('start_date', startDate);
      url.searchParams.set('end_date', endDate);

      const response = await fetch(url);
      const data = await response.json();

      // Filter by room if selected
      const filteredData = selectedRoom
        ? data.filter(event => event.room_name === selectedRoom)
        : data;

      setEvents(filteredData);
    } catch (error) {
      console.error('Failed to fetch reservations:', error);
    } finally {
      setLoading(false);
    }
  }, [currentDate, view, selectedRoom]);

  useEffect(() => {
    fetchReservations();
  }, [fetchReservations]);

  const handlePrev = () => {
    if (view === 'week') {
      setCurrentDate(prev => subWeeks(prev, 1));
    } else {
      setCurrentDate(prev => subMonths(prev, 1));
    }
  };

  const handleNext = () => {
    if (view === 'week') {
      setCurrentDate(prev => addWeeks(prev, 1));
    } else {
      setCurrentDate(prev => addMonths(prev, 1));
    }
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  const handleRoomFilter = (roomName) => {
    setSelectedRoom(prev => prev === roomName ? null : roomName);
  };

  const handleEventClick = (info) => {
    const event = info.event;
    const rect = info.el.getBoundingClientRect();

    setTooltip({
      title: event.extendedProps.room_name,
      username: event.extendedProps.slack_username,
      start: format(new Date(event.start), 'HH:mm'),
      end: format(new Date(event.end), 'HH:mm'),
      date: format(new Date(event.start), 'yyyy년 M월 d일 (EEE)', { locale: ko }),
      x: rect.left + rect.width / 2,
      y: rect.top - 10,
      room: event.extendedProps.room_name,
    });
  };

  const closeTooltip = () => {
    setTooltip(null);
  };

  const getPeriodLabel = () => {
    if (view === 'week') {
      const start = startOfWeek(currentDate, { weekStartsOn: 1 });
      const end = endOfWeek(currentDate, { weekStartsOn: 1 });
      return `${format(start, 'M월 d일', { locale: ko })} - ${format(end, 'M월 d일', { locale: ko })}`;
    } else {
      return format(currentDate, 'yyyy년 M월', { locale: ko });
    }
  };

  const getRoomColor = (roomName) => {
    const room = ROOMS.find(r => r.name === roomName);
    return room?.color || { bg: '#f5f5f5', border: '#9e9e9e', text: '#616161' };
  };

  return (
    <div className="app" onClick={closeTooltip}>
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>
            <span role="img" aria-label="building">🏢</span>
            회의실 예약 현황
          </h1>
          <div className="header-nav">
            <span style={{ opacity: 0.8, fontSize: '0.9rem' }}>
              Delhi | Mumbai | Chennai
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Room Legend */}
        <div className="room-legend">
          {ROOMS.map(room => (
            <div
              key={room.name}
              className={`legend-item ${selectedRoom === room.name ? 'active' : ''}`}
              onClick={() => handleRoomFilter(room.name)}
              style={{
                borderLeft: `4px solid ${room.color.border}`,
                opacity: selectedRoom && selectedRoom !== room.name ? 0.5 : 1,
              }}
            >
              <div
                className={`legend-color ${room.name.toLowerCase()}`}
                style={{
                  backgroundColor: room.color.bg,
                  borderColor: room.color.border,
                }}
              />
              <span style={{ fontWeight: 500 }}>{room.name}</span>
              <span style={{ color: '#666', fontSize: '0.85rem' }}>({room.nameKr})</span>
            </div>
          ))}
          {selectedRoom && (
            <button
              onClick={() => setSelectedRoom(null)}
              style={{
                padding: '0.5rem 1rem',
                background: '#f5f5f5',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.85rem',
              }}
            >
              전체 보기
            </button>
          )}
        </div>

        {/* View Tabs */}
        <div className="view-tabs">
          <button
            className={`view-tab ${view === 'week' ? 'active' : ''}`}
            onClick={() => setView('week')}
          >
            주간 보기
          </button>
          <button
            className={`view-tab ${view === 'month' ? 'active' : ''}`}
            onClick={() => setView('month')}
          >
            월간 보기
          </button>
        </div>

        {/* Navigation Controls */}
        <div className="nav-controls">
          <button className="nav-button" onClick={handlePrev}>
            ← 이전
          </button>
          <button className="nav-button" onClick={handleToday}>
            오늘
          </button>
          <button className="nav-button" onClick={handleNext}>
            다음 →
          </button>
          <span className="current-period">{getPeriodLabel()}</span>
        </div>

        {/* Calendar */}
        <div className="calendar-container">
          {loading ? (
            <div className="loading">
              <div className="loading-spinner" />
            </div>
          ) : (
            <FullCalendar
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
              initialView={view === 'week' ? 'timeGridWeek' : 'dayGridMonth'}
              key={view} // Force re-render on view change
              initialDate={currentDate}
              headerToolbar={false}
              locale="ko"
              firstDay={1}
              slotMinTime="08:00:00"
              slotMaxTime="22:00:00"
              allDaySlot={false}
              weekends={true}
              events={events}
              eventClick={handleEventClick}
              height="auto"
              expandRows={true}
              slotLabelFormat={{
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
              }}
              eventTimeFormat={{
                hour: '2-digit',
                minute: '2-digit',
                hour12: false,
              }}
              dayHeaderFormat={{
                weekday: 'short',
                month: 'numeric',
                day: 'numeric',
              }}
              eventContent={(eventInfo) => {
                const colors = getRoomColor(eventInfo.event.extendedProps.room_name);
                return (
                  <div
                    style={{
                      padding: '2px 4px',
                      overflow: 'hidden',
                      height: '100%',
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: '0.75rem', color: colors.text }}>
                      {eventInfo.event.extendedProps.room_name}
                    </div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.9 }}>
                      {eventInfo.timeText}
                    </div>
                    <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>
                      {eventInfo.event.extendedProps.slack_username}
                    </div>
                  </div>
                );
              }}
            />
          )}
        </div>

        {/* Tooltip */}
        {tooltip && (
          <div
            className="event-tooltip"
            style={{
              left: Math.min(tooltip.x, window.innerWidth - 220),
              top: tooltip.y,
              transform: 'translate(-50%, -100%)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h4>
              <span
                style={{
                  display: 'inline-block',
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  backgroundColor: getRoomColor(tooltip.room).bg,
                  border: `2px solid ${getRoomColor(tooltip.room).border}`,
                  marginRight: 8,
                }}
              />
              {tooltip.title}
            </h4>
            <p>📅 {tooltip.date}</p>
            <p>🕐 {tooltip.start} ~ {tooltip.end}</p>
            <p>👤 {tooltip.username}</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer style={{
        textAlign: 'center',
        padding: '2rem',
        color: '#666',
        fontSize: '0.85rem',
      }}>
        <p>예약은 Slack에서 @봇 도움말 을 입력하세요</p>
      </footer>
    </div>
  );
}

export default App;
