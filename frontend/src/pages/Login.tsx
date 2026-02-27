import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const [phone, setPhone] = useState('')
  const [step, setStep] = useState<'phone' | 'otp'>('phone')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [otpInfo, setOtpInfo] = useState('')

  const { requestOTP, verifyOTP, isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // If already logged in, redirect
  if (isAuthenticated) {
    navigate('/', { replace: true })
  }

  const fullPhone = `234${phone.replace(/\s/g, '').replace(/^0/, '')}`

  const handleRequestOTP = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const result = await requestOTP(fullPhone)
      setOtpInfo(result.message)
      // In dev mode, show debug OTP if delivery failed
      if (result.debug_otp) {
        setOtpInfo(`${result.message}\n\nDev OTP: ${result.debug_otp}`)
      }
      setStep('otp')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to send OTP'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleVerifyOTP = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await verifyOTP(fullPhone, otp)
      navigate('/', { replace: true })
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } }
      setError(apiErr.response?.data?.detail || 'Invalid OTP. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-emerald-600">💵 FinPad</h1>
          <p className="text-gray-500 mt-2">Track your spending, build better habits.</p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          {/* Error message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {error}
            </div>
          )}

          {step === 'phone' ? (
            <form onSubmit={handleRequestOTP} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number
                </label>
                <div className="flex">
                  <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-gray-300 bg-gray-50 text-gray-500 text-sm">
                    +234
                  </span>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="801 234 5678"
                    className="flex-1 block w-full rounded-r-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                    required
                    disabled={loading}
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-emerald-600 text-white py-2.5 rounded-lg font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send OTP via WhatsApp'}
              </button>
              <p className="text-xs text-gray-400 text-center">
                We'll send a verification code to your WhatsApp
              </p>
            </form>
          ) : (
            <form onSubmit={handleVerifyOTP} className="space-y-4">
              <p className="text-sm text-gray-600 text-center">
                Enter the 6-digit code sent to your WhatsApp
              </p>

              {/* Dev info / OTP delivery status */}
              {otpInfo && (
                <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-600 whitespace-pre-line">
                  {otpInfo}
                </div>
              )}

              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                placeholder="Enter OTP"
                maxLength={6}
                className="block w-full text-center text-2xl tracking-widest rounded-lg border border-gray-300 px-3 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
                disabled={loading}
                autoFocus
              />
              <button
                type="submit"
                disabled={loading || otp.length < 6}
                className="w-full bg-emerald-600 text-white py-2.5 rounded-lg font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify & Login'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setStep('phone')
                  setOtp('')
                  setError('')
                  setOtpInfo('')
                }}
                className="w-full text-sm text-gray-500 hover:text-gray-700"
              >
                ← Change phone number
              </button>
            </form>
          )}
        </div>

        <p className="text-xs text-gray-400 text-center mt-6">
          Also available on WhatsApp — just message us to get started!
        </p>
      </div>
    </div>
  )
}
