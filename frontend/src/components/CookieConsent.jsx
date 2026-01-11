import React, { useState, useEffect } from 'react'

export default function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem('finance_cookie_consent')
    if (!consent) {
      setShowBanner(true)
    }
  }, [])

  const handleAcceptAll = () => {
    localStorage.setItem('finance_cookie_consent', JSON.stringify({
      essential: true,
      analytics: true,
      marketing: true,
      timestamp: new Date().toISOString()
    }))
    setShowBanner(false)
  }

  const handleRejectOptional = () => {
    localStorage.setItem('finance_cookie_consent', JSON.stringify({
      essential: true,
      analytics: false,
      marketing: false,
      timestamp: new Date().toISOString()
    }))
    setShowBanner(false)
  }

  const handleCustomize = () => {
    setShowDetails(!showDetails)
  }

  if (!showBanner) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-blue-600 shadow-2xl">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-2">Ihre Einstellung zu Cookies</h3>
              <div className="text-sm text-gray-700 space-y-3">
                <p>
                  Wenn Sie über 16 Jahre sind, klicken Sie auf „Ich bin einverstanden", um allen Verarbeitungszwecken zuzustimmen.
                  Hier finden Sie nähere Informationen zu unseren wesentlichen Cookies (für die Funktion der Internetseite unerlässlich),
                  sowie optionalen Werbe- (personalisierte Werbung, Surfverhalten) und Statistik-Cookies (Nutzerverhalten, Serviceverbesserung).
                  Einzelne Kategorien können Sie auch ablehnen. Ihre Cookie-Einstellungen können Sie jederzeit ändern.
                </p>

                {showDetails && (
                  <>
                    <p className="bg-yellow-50 border-l-4 border-yellow-400 p-3 text-xs">
                      <strong>Hinweis zu Datenübermittlungen in die USA:</strong> Einige unserer Partnerdienste befinden sich in den USA.
                      Nach Rechtsprechung des Europäischen Gerichtshofs existiert derzeit in den USA kein angemessener Datenschutz.
                      Es besteht das Risiko, dass Ihre Daten durch US-Behörden kontrolliert und überwacht werden.
                      Dagegen können Sie keine wirksamen Rechtsmittel vorbringen.
                    </p>

                    <div className="bg-gray-50 p-4 rounded-lg text-xs space-y-2">
                      <h4 className="font-semibold text-gray-900">Gemeinsame Verantwortlichkeiten gemäß DSGVO:</h4>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        <li>Ihre Einwilligung und die einzelnen Einstellungen gelten gemeinsam für den Webauftritt von Finance auf finance.app.</li>
                        <li>Mit Analysediensten besteht eine gemeinsame Verantwortlichkeit hinsichtlich Erhebung und Übermittlung personenbezogener Daten.</li>
                      </ul>
                      <p className="mt-2">
                        Weiterführende Informationen zum Datenschutz, auch zur gemeinsamen Verantwortlichkeit, finden Sie in unserer{' '}
                        <a href="/datenschutz" className="text-blue-600 hover:text-blue-700 underline">Datenschutzerklärung</a>.
                      </p>
                    </div>

                    {/* Cookie Categories */}
                    <div className="space-y-3 mt-4">
                      <div className="bg-white border border-gray-200 rounded p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h5 className="font-semibold text-gray-900">Essenzielle Cookies</h5>
                            <p className="text-xs text-gray-600">Für die Funktion der Website unerlässlich</p>
                          </div>
                          <span className="text-xs px-3 py-1 bg-gray-200 text-gray-700 rounded">Erforderlich</span>
                        </div>
                      </div>

                      <div className="bg-white border border-gray-200 rounded p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h5 className="font-semibold text-gray-900">Statistik-Cookies</h5>
                            <p className="text-xs text-gray-600">Nutzerverhalten verstehen, Service verbessern</p>
                          </div>
                          <span className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded">Optional</span>
                        </div>
                      </div>

                      <div className="bg-white border border-gray-200 rounded p-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <h5 className="font-semibold text-gray-900">Werbe-Cookies</h5>
                            <p className="text-xs text-gray-600">Personalisierte Werbung basierend auf Surfverhalten</p>
                          </div>
                          <span className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded">Optional</span>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <button
              onClick={handleAcceptAll}
              className="w-full sm:w-auto px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold"
            >
              Ich bin einverstanden
            </button>
            <button
              onClick={handleRejectOptional}
              className="w-full sm:w-auto px-6 py-3 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 transition-all font-semibold"
            >
              Nur essenzielle Cookies
            </button>
            <button
              onClick={handleCustomize}
              className="w-full sm:w-auto px-6 py-3 bg-white text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition-all font-semibold"
            >
              {showDetails ? 'Details ausblenden' : 'Details anzeigen'}
            </button>
          </div>

          <p className="text-xs text-gray-500 text-center">
            Mit der Nutzung dieser Website stimmen Sie der Verwendung von Cookies zu.{' '}
            <a href="/datenschutz" className="text-blue-600 hover:text-blue-700 underline">Mehr erfahren</a>
          </p>
        </div>
      </div>
    </div>
  )
}

