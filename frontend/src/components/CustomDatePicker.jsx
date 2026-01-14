import React, { useState, useRef, useEffect } from 'react'
import { dateToInputFormat, inputDateToISO, getFormatPreferences, formatDate } from '../utils/format'
import { useTranslate } from '../hooks/useLanguage'

/**
 * CustomDatePicker Component
 * A fully styled, custom date picker with calendar UI
 * Supports multiple languages and configurable date formats
 *
 * Features:
 * - Custom calendar UI (not relying on browser native)
 * - Text input for manual date entry in user's preferred format
 * - Month/year navigation
 * - Fully themeable with Tailwind CSS
 * - Multilingual support (EN, DE, easily extensible)
 * - Keyboard navigation
 * - Works reliably everywhere (modals, etc.)
 *
 * @param {string} value - ISO format date (YYYY-MM-DD)
 * @param {function} onChange - Callback when date changes (receives ISO format)
 * @param {string} placeholder - Input placeholder text (optional)
 * @param {string} title - Tooltip text
 * @param {boolean} showPickerButton - Whether to show date picker button (default: true)
 * @param {string} className - Additional CSS classes
 */
export default function CustomDatePicker({
  value,
  onChange,
  placeholder,
  title = 'Enter date in your preferred format',
  showPickerButton = true,
  className = '',
}) {
  const [displayValue, setDisplayValue] = useState(dateToInputFormat(value || ''))
  const [showCalendar, setShowCalendar] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(() => {
    if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
      const [year, month] = value.split('-')
      return new Date(parseInt(year), parseInt(month) - 1)
    }
    return new Date()
  })
  const calendarRef = useRef(null)
  const prefs = getFormatPreferences()
  const t = useTranslate()

  // Month names for different languages
  const monthNames = {
    en: ['January', 'February', 'March', 'April', 'May', 'June',
         'July', 'August', 'September', 'October', 'November', 'December'],
    de: ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
         'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
  }

  // Day names for different languages
  const dayNames = {
    en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    de: ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'],
  }

  const currentLanguage = prefs.language === 'de' ? 'de' : 'en'
  const months = monthNames[currentLanguage]
  const days = dayNames[currentLanguage]

  const getDefaultPlaceholder = () => {
    return prefs.dateFormat
  }

  const defaultPlaceholder = getDefaultPlaceholder()

  useEffect(() => {
    setDisplayValue(dateToInputFormat(value || ''))
  }, [value])

  // Close calendar when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (calendarRef.current && !calendarRef.current.contains(event.target)) {
        setShowCalendar(false)
      }
    }

    if (showCalendar) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showCalendar])

  const handleTextChange = (e) => {
    const inputValue = e.target.value
    setDisplayValue(inputValue)

    if (inputValue.trim().length > 0) {
      const isoDate = inputDateToISO(inputValue)
      if (isoDate && isoDate !== inputValue && /^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
        onChange(isoDate)
        // Update calendar to show the selected month
        const [year, month] = isoDate.split('-')
        setCurrentMonth(new Date(parseInt(year), parseInt(month) - 1))
      }
    }
  }

  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate()
  }

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay()
  }

  const handleDayClick = (day) => {
    const year = currentMonth.getFullYear()
    const month = String(currentMonth.getMonth() + 1).padStart(2, '0')
    const dayStr = String(day).padStart(2, '0')
    const isoDate = `${year}-${month}-${dayStr}`

    setDisplayValue(dateToInputFormat(isoDate))
    onChange(isoDate)
    setShowCalendar(false)
  }

  const handlePrevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))
  }

  const handleNextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))
  }

  const renderCalendarDays = () => {
    const daysInMonth = getDaysInMonth(currentMonth)
    const firstDay = getFirstDayOfMonth(currentMonth)
    const days = []

    // Empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="h-8"></div>)
    }

    // Days of month
    for (let day = 1; day <= daysInMonth; day++) {
      const year = currentMonth.getFullYear()
      const month = String(currentMonth.getMonth() + 1).padStart(2, '0')
      const dayStr = String(day).padStart(2, '0')
      const dateStr = `${year}-${month}-${dayStr}`
      const isSelected = value === dateStr
      const isToday = dateStr === new Date().toISOString().split('T')[0]

      days.push(
        <button
          key={day}
          onClick={() => handleDayClick(day)}
          className={`h-8 rounded text-sm font-medium transition-colors ${
            isSelected
              ? 'bg-blue-600 text-white'
              : isToday
              ? 'border border-blue-500 text-blue-600'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          {day}
        </button>
      )
    }

    return days
  }

  return (
    <div className={`relative ${className}`} ref={calendarRef}>
      <div className="flex items-center gap-2">
        {/* Text input for manual entry */}
        <input
          type="text"
          value={displayValue}
          onChange={handleTextChange}
          placeholder={placeholder || defaultPlaceholder}
          title={title}
          className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoComplete="off"
        />

        {/* Calendar button */}
        {showPickerButton && (
          <button
            type="button"
            onClick={() => setShowCalendar(!showCalendar)}
            className="px-3 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded text-gray-700 font-medium transition-colors flex-shrink-0 cursor-pointer"
            title="Open date picker"
            aria-label="Open calendar date picker"
          >
            📅
          </button>
        )}
      </div>

      {/* Calendar modal */}
      {showCalendar && (
        <div className="absolute z-50 mt-2 bg-white border border-gray-300 rounded-lg shadow-lg p-4 w-72">
          {/* Header with month/year and navigation */}
          <div className="flex items-center justify-between mb-4">
            <button
              type="button"
              onClick={handlePrevMonth}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title="Previous month"
            >
              ←
            </button>
            <h3 className="font-semibold text-gray-900 text-sm">
              {months[currentMonth.getMonth()]} {currentMonth.getFullYear()}
            </h3>
            <button
              type="button"
              onClick={handleNextMonth}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title="Next month"
            >
              →
            </button>
          </div>

          {/* Day names header */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {days.map((day) => (
              <div key={day} className="h-8 flex items-center justify-center text-xs font-semibold text-gray-600">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {renderCalendarDays()}
          </div>

          {/* Footer with today button */}
          <div className="mt-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={() => {
                const today = new Date().toISOString().split('T')[0]
                setDisplayValue(dateToInputFormat(today))
                onChange(today)
                setShowCalendar(false)
              }}
              className="w-full py-2 px-3 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded text-sm font-medium transition-colors"
            >
              {currentLanguage === 'de' ? 'Heute' : 'Today'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

