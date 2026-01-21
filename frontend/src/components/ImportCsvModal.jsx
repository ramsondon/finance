import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { getCsrfToken } from '../utils/csrf'
import { useTranslate } from '../hooks/useLanguage'
import { Upload, Loader, AlertCircle, CheckCircle, FileText, FileCode, X, ArrowRight, ArrowLeft } from 'lucide-react'

export default function ImportModal({ onClose }) {
  const t = useTranslate()
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState('')
  const [file, setFile] = useState(null)
  const [step, setStep] = useState(1) // 1: Upload, 2: Map fields, 3: Import result
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // Mapping state
  const [fileFields, setFileFields] = useState([])
  const [sampleData, setSampleData] = useState([])
  const [transactionFields, setTransactionFields] = useState([])
  const [fieldMappings, setFieldMappings] = useState({}) // { transactionField: fileField }
  const [fileType, setFileType] = useState('')

  // ESC key handler to close modal
  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [onClose])

  useEffect(() => {
    axios.get('/api/banking/accounts/')
      .then(res => {
        const accts = res.data.results || res.data || []
        setAccounts(accts)
        if (accts.length > 0) setSelectedAccount(accts[0].id)
      })
      .catch(() => setAccounts([]))
  }, [])

  // Auto-map fields when file is previewed
  const autoMapFields = (txFields, fFields) => {
    const mappings = {}
    const fileFieldsLower = fFields.map(f => f.toLowerCase())

    txFields.forEach(txField => {
      // Skip description - it's auto-derived from reference
      if (txField.name === 'description') return

      // Try exact match first
      const exactMatch = fFields.find(f => f.toLowerCase() === txField.name.toLowerCase())
      if (exactMatch) {
        mappings[txField.name] = exactMatch
        return
      }

      // Try target property match
      const targetMatch = fFields.find(f => f.toLowerCase() === txField.target_property.toLowerCase())
      if (targetMatch) {
        mappings[txField.name] = targetMatch
        return
      }

      // Try common aliases (including dot notation for nested JSON)
      const aliases = {
        'date': ['date', 'booking', 'transactiondate', 'transaction_date', 'bookingdate', 'valuation', 'datum'],
        'amount': ['amount', 'value', 'sum', 'betrag', 'amount.value'],
        'reference': ['reference', 'ref', 'referenz', 'booking_text', 'description', 'text', 'verwendungszweck', 'details', 'memo', 'buchungstext'],
        'reference_number': ['reference_number', 'referencenumber', 'reference.no', 'referenznummer'],
        'valuation_date': ['valuation_date','valuationdate', 'valuedate', 'value_date', 'valuta', 'valuation', 'bewertungsdatum'],
        'virtual_card_number': ['virtualcardnumber', 'virtual_card_number', 'vcn', 'virtualcard.number'],
        'virtual_card_device': ['virtualcarddevice', 'virtual_card_device', 'vcarddevice', 'virtualcard.device'],
        'payment_app': ['paymentapp', 'payment_app', 'paymentapplication'],
        'card_brand': ['cardbrand', 'card_brand', 'cardtype', 'kartentyp'],
        'exchange_rate': ['exchangerate', 'exchange_rate', 'fxrate', 'waehrungskurs'],
        'transaction_fee': ['transactionfee', 'transaction_fee', 'fee', 'gebuehr'],
        'sepa_scheme': ['sepascheme', 'sepa_scheme', 'sepa'],
        'partner_name': ['partnername', 'partner_name', 'counterparty', 'recipient', 'sender', 'empfaenger', 'auftraggeber'],
        'partner_iban': ['partneriban', 'partner_iban', 'iban', 'counterparty_iban', 'partneraccount.iban'],
        'partner_account': ['partneraccount.number', 'kontonummer', 'partneraccount', 'partner_account'],
        'partner_bank_code': ['partneraccount.bankcode', 'partnerbankcode', 'partner_bank_code'],
        'owner_account': ['owneraccount.number', 'owner_account_number', 'owneraccountnumber', 'eigentuemerkontonummer'],
        'owner_name': ['ownername', 'owner_name', 'owneraccounttitle', 'eigentuemerkontoname'],
        'booking_type': ['bookingtype', 'booking_type', 'bookingtypetranslation', 'transactiontype', 'buchungsart'],
        'booking_date': ['booking_date', 'buchungsdatum', 'booking', 'bookingdate'],
        'merchant_name': ['merchantname', 'merchant_name', 'merchant', 'haendler'],
        'payment_method': ['paymentmethod', 'payment_method', 'zahlungsart'],
      }

      const fieldAliases = aliases[txField.name] || []
      for (const alias of fieldAliases) {
        const idx = fileFieldsLower.findIndex(f => f.replace(/[_\s.]/g, '').includes(alias.replace(/[_\s.]/g, '')))
        if (idx !== -1) {
          mappings[txField.name] = fFields[idx]
          return
        }
      }
    })

    return mappings
  }

  const handleFilePreview = async () => {
    if (!file || !selectedAccount) return

    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('account', selectedAccount)

    try {
      const res = await axios.post('/api/banking/transactions/preview-file/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': getCsrfToken()
        }
      })

      setFileFields(res.data.file_fields)
      setSampleData(res.data.sample_data)
      setTransactionFields(res.data.transaction_fields)
      setFileType(res.data.file_type)

      // Use saved mappings if available, otherwise auto-map
      const savedMappings = res.data.saved_mappings || {}
      if (Object.keys(savedMappings).length > 0) {
        // Convert saved mappings (fileField -> targetProperty) back to (txFieldName -> fileField)
        const restoredMappings = {}
        res.data.transaction_fields.forEach(txField => {
          // Find which file field maps to this transaction field's target property
          for (const [fileField, targetProp] of Object.entries(savedMappings)) {
            if (targetProp === txField.target_property && res.data.file_fields.includes(fileField)) {
              restoredMappings[txField.name] = fileField
              break
            }
          }
        })
        // Merge with auto-mappings for any missing fields
        const autoMappings = autoMapFields(res.data.transaction_fields, res.data.file_fields)
        setFieldMappings({ ...autoMappings, ...restoredMappings })
      } else {
        // Auto-map fields
        const autoMappings = autoMapFields(res.data.transaction_fields, res.data.file_fields)
        setFieldMappings(autoMappings)
      }

      setStep(2)
    } catch (err) {
      setError(err.response?.data?.message || err.message || t('import.previewFailed'))
    } finally {
      setUploading(false)
    }
  }

  const handleImport = async () => {
    if (!file || !selectedAccount) return

    // Validate required fields are mapped
    const requiredFields = transactionFields.filter(f => f.required)
    const missingRequired = requiredFields.filter(f => !fieldMappings[f.name])

    if (missingRequired.length > 0) {
      setError(t('import.missingRequiredFields', { fields: missingRequired.map(f => f.name).join(', ') }))
      return
    }

    setUploading(true)
    setError(null)
    setResult(null)
    setSuccess(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('account', selectedAccount)

    // Convert mappings to format expected by backend: { fileField: transactionProperty }
    const backendMappings = {}
    Object.entries(fieldMappings).forEach(([txField, fileField]) => {
      if (fileField) {
        const txFieldInfo = transactionFields.find(f => f.name === txField)
        if (txFieldInfo) {
          backendMappings[fileField] = txFieldInfo.target_property
        }
      }
    })
    formData.append('field_mappings', JSON.stringify(backendMappings))

    try {
      const res = await axios.post('/api/banking/transactions/import-transactions/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'X-CSRFToken': getCsrfToken()
        }
      })
      setResult(res.data)
      setStep(3)

      // Only auto-close if transactions were successfully queued and no errors
      if (res.data.queued > 0 && (!res.data.errors || res.data.errors.length === 0)) {
        setSuccess(t('import.successMessage', { count: res.data.queued, type: res.data.file_type.toUpperCase() }))
        setTimeout(() => onClose(), 2500)
      } else if (res.data.queued > 0) {
        // Some transactions queued but with errors - don't auto-close
        setSuccess(t('import.successMessage', { count: res.data.queued, type: res.data.file_type.toUpperCase() }))
      } else {
        // No transactions queued - show as error state
        setError(t('import.noValidTransactions'))
      }
    } catch (err) {
      setError(err.response?.data?.message || err.message || t('import.importFailed'))
    } finally {
      setUploading(false)
    }
  }

  const updateMapping = (txFieldName, fileField) => {
    setFieldMappings(prev => ({
      ...prev,
      [txFieldName]: fileField || ''
    }))
  }

  const getSampleValue = (fileField) => {
    if (!fileField || sampleData.length === 0) return ''
    const firstRow = sampleData[0]
    if (typeof firstRow === 'object' && firstRow !== null) {
      const value = firstRow[fileField]
      if (value === null || value === undefined) return ''
      // If value is an object, stringify it for display
      if (typeof value === 'object') {
        return JSON.stringify(value)
      }
      return String(value)
    }
    return ''
  }

  const getFieldDisplayName = (name) => {
    const displayNames = {
      'date': t('import.fields.date'),
      'amount': t('import.fields.amount'),
      'description': t('import.fields.description'),
      'reference': t('import.fields.reference'),
      'booking_type': t('import.fields.bookingType'),
      'partner_name': t('import.fields.partnerName'),
      'partner_iban': t('import.fields.partnerIban'),
      'partner_account': t('import.fields.partnerAccount'),
      'partner_bank_code': t('import.fields.partnerBankCode'),
      'merchant_name': t('import.fields.merchantName'),
      'owner_account': t('import.fields.ownerAccount'),
      'owner_name': t('import.fields.ownerName'),
      'booking_date': t('import.fields.bookingDate'),
      'valuation_date': t('import.fields.valuationDate'),
      'reference_number': t('import.fields.referenceNumber'),
      'virtual_card_number': t('import.fields.virtualCardNumber'),
      'virtual_card_device': t('import.fields.virtualCardDevice'),
      'payment_app': t('import.fields.paymentApp'),
      'payment_method': t('import.fields.paymentMethod'),
      'card_brand': t('import.fields.cardBrand'),
      'exchange_rate': t('import.fields.exchangeRate'),
      'transaction_fee': t('import.fields.transactionFee'),
      'sepa_scheme': t('import.fields.sepaScheme'),
    }
    return displayNames[name] || name
  }

  // Separate required and optional fields (exclude description as it's auto-derived from reference)
  const requiredFields = transactionFields.filter(f => f.required)
  const optionalFields = transactionFields.filter(f => !f.required && f.name !== 'description')

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl border border-gray-200 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 shrink-0">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{t('import.title')}</h2>
            <p className="text-sm text-gray-500">
              {step === 1 && t('import.step1Description')}
              {step === 2 && t('import.step2Description')}
              {step === 3 && t('import.step3Description')}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {/* Step Indicator */}
        <div className="px-6 py-3 border-b border-gray-100 bg-gray-50 shrink-0">
          <div className="flex items-center justify-between">
            <div className={`flex items-center gap-2 ${step >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>1</div>
              <span className="text-sm font-medium">{t('import.stepUpload')}</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200">
              <div className={`h-full ${step >= 2 ? 'bg-blue-600' : 'bg-gray-200'} transition-all`} style={{ width: step >= 2 ? '100%' : '0%' }}></div>
            </div>
            <div className={`flex items-center gap-2 ${step >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>2</div>
              <span className="text-sm font-medium">{t('import.stepMapFields')}</span>
            </div>
            <div className="flex-1 mx-4 h-0.5 bg-gray-200">
              <div className={`h-full ${step >= 3 ? 'bg-blue-600' : 'bg-gray-200'} transition-all`} style={{ width: step >= 3 ? '100%' : '0%' }}></div>
            </div>
            <div className={`flex items-center gap-2 ${step >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${step >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>3</div>
              <span className="text-sm font-medium">{t('import.stepComplete')}</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Step 1: Upload File */}
          {step === 1 && (
            <div className="space-y-4">
              {/* Account Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('import.bankAccount')}
                </label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {accounts.length === 0 ? (
                    <option value="">{t('import.noAccounts')}</option>
                  ) : (
                    accounts.map(acc => (
                      <option key={acc.id} value={acc.id}>
                        {acc.name} ({acc.currency})
                      </option>
                    ))
                  )}
                </select>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('import.selectFile')}
                </label>
                <div className="relative">
                  <input
                    type="file"
                    accept=".csv,.json"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500 space-y-1">
                  <div className="flex items-center gap-1"><FileText size={14} className="text-gray-400" /> <strong>CSV:</strong> {t('import.csvDescription')}</div>
                  <div className="flex items-center gap-1"><FileCode size={14} className="text-gray-400" /> <strong>JSON:</strong> {t('import.jsonDescription')}</div>
                </p>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center gap-2">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}
            </div>
          )}

          {/* Step 2: Map Fields */}
          {step === 2 && (
            <div className="space-y-6">
              {/* File Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                <div className="font-medium">{t('import.fileDetected', { type: fileType.toUpperCase(), count: fileFields.length })}</div>
              </div>

              {/* Required Fields */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <span className="text-red-500">*</span> {t('import.requiredFields')}
                </h3>
                <div className="space-y-3">
                  {requiredFields.map(field => (
                    <div key={field.name} className="grid grid-cols-2 gap-4 items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-700">{getFieldDisplayName(field.name)}</span>
                        <span className="text-xs text-gray-400">({field.data_type})</span>
                      </div>
                      <div>
                        <select
                          value={fieldMappings[field.name] || ''}
                          onChange={(e) => updateMapping(field.name, e.target.value)}
                          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm ${
                            !fieldMappings[field.name] ? 'border-red-300 bg-red-50' : 'border-gray-300'
                          }`}
                        >
                          <option value="">{t('import.selectField')}</option>
                          {fileFields.map(ff => (
                            <option key={ff} value={ff}>{ff}</option>
                          ))}
                        </select>
                        {fieldMappings[field.name] && (
                          <div className="mt-1 text-xs text-gray-500 truncate">
                            {t('import.sampleValue')}: {getSampleValue(fieldMappings[field.name])}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Optional Fields */}
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">{t('import.optionalFields')}</h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {optionalFields.map(field => (
                    <div key={field.name} className="grid grid-cols-2 gap-4 items-center">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-700">{getFieldDisplayName(field.name)}</span>
                        <span className="text-xs text-gray-400">({field.data_type})</span>
                      </div>
                      <div>
                        <select
                          value={fieldMappings[field.name] || ''}
                          onChange={(e) => updateMapping(field.name, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                        >
                          <option value="">{t('import.leaveEmpty')}</option>
                          {fileFields.map(ff => (
                            <option key={ff} value={ff}>{ff}</option>
                          ))}
                        </select>
                        {fieldMappings[field.name] && (
                          <div className="mt-1 text-xs text-gray-500 truncate">
                            {t('import.sampleValue')}: {getSampleValue(fieldMappings[field.name])}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center gap-2">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}
            </div>
          )}

          {/* Step 3: Import Complete */}
          {step === 3 && (
            <div className="space-y-4">
              {success && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle size={20} />
                    <span className="font-medium">{t('import.importComplete')}</span>
                  </div>
                  <p>{success}</p>
                </div>
              )}

              {result && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                  <div className="font-medium mb-1">{t('import.importDetails')}</div>
                  <div className="flex items-center gap-1">
                    <CheckCircle size={14} className="text-green-600" />
                    {t('import.transactionsQueued', { count: result.queued })}
                  </div>
                  {result.errors?.length > 0 && (
                    <div className="mt-2">
                      <div className="text-red-600 flex items-center gap-1 mb-1">
                        <AlertCircle size={14} />
                        {t('import.rowsWithErrors', { count: result.errors.length })}
                      </div>
                      <div className="text-xs text-red-500 max-h-32 overflow-y-auto bg-red-50 p-2 rounded">
                        {result.errors.slice(0, 10).map((err, i) => (
                          <div key={i}>{err}</div>
                        ))}
                        {result.errors.length > 10 && <div>... and {result.errors.length - 10} more errors</div>}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700 flex items-center gap-2">
                  <AlertCircle size={16} />
                  {error}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 shrink-0">
          <div className="flex gap-3 justify-end">
            {step === 1 && (
              <>
                <button
                  type="button"
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={handleFilePreview}
                  disabled={uploading || !file || !selectedAccount}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader size={18} className="animate-spin" />
                      {t('import.analyzing')}
                    </>
                  ) : (
                    <>
                      {t('import.continue')}
                      <ArrowRight size={18} />
                    </>
                  )}
                </button>
              </>
            )}

            {step === 2 && (
              <>
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="px-4 py-2 bg-gray-100 text-gray-900 rounded-lg hover:bg-gray-200 font-medium transition-colors flex items-center gap-2"
                >
                  <ArrowLeft size={18} />
                  {t('import.back')}
                </button>
                <button
                  onClick={handleImport}
                  disabled={uploading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors flex items-center gap-2"
                >
                  {uploading ? (
                    <>
                      <Loader size={18} className="animate-spin" />
                      {t('import.importing')}
                    </>
                  ) : (
                    <>
                      <Upload size={18} />
                      {t('import.startImport')}
                    </>
                  )}
                </button>
              </>
            )}

            {step === 3 && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
              >
                {t('common.close')}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
