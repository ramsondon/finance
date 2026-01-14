import React, { useState, useRef, useEffect } from 'react'
import { dateToInputFormat, inputDateToISO, getFormatPreferences } from '../utils/format'

/**
 * DateInput Component
 * Provides both a text input (user-friendly format) and a hidden HTML date picker
 *
 * Features:
 * - Display dates in user's preferred format
 * - Accept dates in user's preferred format
 * - Optional date picker button for calendar selection
 * - Automatic format conversion
 *
 * @param {string} value - ISO format date (YYYY-MM-DD)
 * @param {function} onChange - Callback when date changes (receives ISO format)
 * @param {string} placeholder - Input placeholder text
 * @param {string} title - Tooltip text
 * @param {boolean} showPickerButton - Whether to show date picker button (default: true)
 * @param {string} className - Additional CSS classes
 */
export default function DateInput({
  value,
  onChange,
  placeholder = 'MM/DD/YYYY',
  title = 'Enter date in your preferred format',
  showPickerButton = true,
  className = '',
}) {
  const [displayValue, setDisplayValue] = useState(dateToInputFormat(value))
  const datePickerRef = useRef(null)
  const prefs = getFormatPreferences()

  // Update display value when prop changes (e.g., when editing existing record)
  useEffect(() => {
    setDisplayValue(dateToInputFormat(value))
  }, [value])

  const handleTextChange = (e) => {
    const inputValue = e.target.value
    setDisplayValue(inputValue)
    // Convert to ISO and call onChange
    const isoDate = inputDateToISO(inputValue)
    if (isoDate) {
      onChange(isoDate)
    }
  }

  const handlePickerChange = (e) => {
    // Date picker returns ISO format directly
    const isoDate = e.target.value
    if (isoDate) {
      // Convert to display format
      setDisplayValue(dateToInputFormat(isoDate))
      onChange(isoDate)
    }
  }

  const openDatePicker = () => {
    if (datePickerRef.current) {
      datePickerRef.current.click()
    }
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <input
        type="text"
        value={displayValue}
        onChange={handleTextChange}
        placeholder={placeholder}
        title={title}
        className="flex-1 border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {/* Hidden date picker input */}
      <input
        ref={datePickerRef}
        type="date"
        value={value || ''}
        onChange={handlePickerChange}
        style={{ display: 'none' }}
      />

      {/* Calendar picker button */}
      {showPickerButton && (
        <button
          type="button"
          onClick={openDatePicker}
          className="px-3 py-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded text-gray-700 font-medium transition-colors"
          title="Open date picker"
          aria-label="Open calendar date picker"
        >
          📅
        </button>
      )}
    </div>
  )
}

