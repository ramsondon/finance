import React from 'react'
import CookieConsent from './CookieConsent'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      {/* Navigation */}
      <nav className="border-b border-gray-200 bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img
              src="/static/img/finance_forecast_logo.png"
              alt="Finance Logo"
              className="w-10 h-10 rounded-lg"
            />
            <span className="text-2xl font-bold text-gray-900">Finance</span>
          </div>
          <div className="flex items-center space-x-4">
            <a href="#features" className="text-gray-600 hover:text-gray-900 transition-colors">Features</a>
            <a href="#about" className="text-gray-600 hover:text-gray-900 transition-colors">About</a>
            <a href="/login" className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold">
              Sign In
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight text-gray-900">
          Smart Financial
          <span className="text-blue-600"> Management</span>
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
          Take control of your finances with our intelligent dashboard. Track spending, analyze trends, and get AI-powered insights to help you make smarter financial decisions.
        </p>

        <div className="flex flex-col md:flex-row items-center justify-center gap-6 mb-16">
          <a
            href="/login"
            className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold text-lg"
          >
            Get Started Now
          </a>
          <a
            href="#features"
            className="px-8 py-4 bg-white hover:bg-gray-100 rounded-lg transition-all font-semibold text-lg border border-gray-300 text-gray-900"
          >
            Learn More
          </a>
        </div>

        {/* Hero Image Placeholder */}
        <div className="relative h-96 md:h-[500px] rounded-2xl overflow-hidden border border-gray-700 bg-gradient-to-b from-gray-800 to-gray-900">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-8xl mb-4 animate-bounce">📊</div>
              <p className="text-gray-400">Dashboard Preview Coming Soon</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">Powerful Features</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {[
            {
              icon: '💳',
              title: 'Multi-Account Support',
              description: 'Manage multiple bank accounts in one place. Track all your finances from a single dashboard.'
            },
            {
              icon: '📊',
              title: 'Real-time Analytics',
              description: 'Get instant insights into your spending habits with beautiful charts and visualizations.'
            },
            {
              icon: '🤖',
              title: 'AI Insights',
              description: 'Powered by advanced AI, get personalized recommendations to improve your financial health.'
            },
            {
              icon: '📈',
              title: 'Smart Categorization',
              description: 'Automatic transaction categorization with customizable rules. Stay organized effortlessly.'
            },
            {
              icon: '📥',
              title: 'Easy CSV Import',
              description: 'Import transactions from your bank statements with just a few clicks.'
            },
            {
              icon: '🔒',
              title: 'Secure & Private',
              description: 'Your financial data is protected with enterprise-grade security and encryption.'
            }
          ].map((feature, i) => (
            <div
              key={i}
              className="bg-gradient-to-b from-gray-800 to-gray-900 rounded-2xl p-8 border border-gray-700 hover:border-blue-500/50 transition-all hover:shadow-xl hover:shadow-blue-500/20"
            >
              <div className="text-5xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-gray-400">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 max-w-4xl mx-auto px-6 py-20">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-12 text-center">
          <h2 className="text-4xl font-bold mb-4">Ready to take control?</h2>
          <p className="text-xl text-gray-100 mb-8">Start managing your finances smarter today with just one click.</p>
          <a
            href="/login"
            className="inline-block px-8 py-4 bg-white text-blue-600 rounded-xl hover:shadow-2xl transition-all font-bold text-lg"
          >
            Sign In with Google
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-700/50 mt-20 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center text-lg font-bold">
                  💰
                </div>
                <span className="font-bold">Finance</span>
              </div>
              <p className="text-gray-400 text-sm">Smart financial management for everyone.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Cookies</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-700 pt-8 text-center text-gray-400 text-sm">
            <p>&copy; 2026 Finance. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* Cookie Consent Banner */}
      <CookieConsent />
    </div>
  )
}
