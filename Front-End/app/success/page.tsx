"use client"

import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { QRCodeSVG } from "qrcode.react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, MessageCircle, Smartphone } from "lucide-react"
import Link from "next/link"

// Force this page to be dynamically rendered, not statically cached
export const dynamic = 'force-dynamic'

function SuccessPageContent() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session_id")
  
  const whatsappNumber = process.env.NEXT_PUBLIC_WA_BUSINESS_NUMBER || "1234567890"
  const activationMessage = `POSITIVITY-PUSH START ${sessionId || "DEMO"}`
  const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(activationMessage)}`

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <MessageCircle className="w-8 h-8 text-red-600" />
            </div>
            <CardTitle className="text-red-600">Invalid Access</CardTitle>
            <CardDescription>
              This page requires a valid session ID. Please complete your payment first.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Link href="/">
              <Button variant="outline" className="w-full">
                Return to Home
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl mx-auto">
        <Card className="w-full">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <CardTitle className="text-3xl font-bold text-gray-900">
              Payment Successful! 🎉
            </CardTitle>
            <CardDescription className="text-lg mt-2">
              Welcome to Positivity Push! Let's activate your personal AI coach.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-8">
            {/* Instructions */}
            <div className="bg-blue-50 rounded-lg p-6 text-center">
              <h3 className="font-semibold text-lg mb-4 text-blue-900">
                🚀 Activate Your AI Coach in 2 Steps:
              </h3>
              <div className="space-y-3 text-left max-w-md mx-auto">
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
                  <p className="text-sm">Click the WhatsApp button below or scan the QR code</p>
                </div>
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
                  <p className="text-sm">Tap "Send" in WhatsApp to start your coaching!</p>
                </div>
              </div>
            </div>

            {/* Mobile-First Design */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* QR Code Section */}
              <div className="text-center order-2 md:order-1">
                <h4 className="font-semibold mb-4 flex items-center justify-center gap-2 text-gray-700">
                  <Smartphone className="w-5 h-5" />
                  Scan with Phone
                </h4>
                <div className="bg-white p-6 rounded-xl border-2 border-dashed border-gray-300 inline-block shadow-sm">
                  <QRCodeSVG 
                    value={whatsappUrl}
                    size={180}
                    level="M"
                    includeMargin={true}
                  />
                </div>
                <p className="text-sm text-gray-600 mt-3">
                  Point your camera at this QR code
                </p>
              </div>

              {/* WhatsApp Button Section */}
              <div className="text-center order-1 md:order-2">
                <h4 className="font-semibold mb-4 flex items-center justify-center gap-2 text-gray-700">
                  <MessageCircle className="w-5 h-5" />
                  Click to Open WhatsApp
                </h4>
                <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" className="block">
                  <Button size="lg" className="w-full max-w-sm bg-green-600 hover:bg-green-700 text-white text-lg py-4 rounded-xl shadow-lg hover:shadow-xl transition-all">
                    <MessageCircle className="w-6 h-6 mr-3" />
                    Activate AI Coach
                  </Button>
                </a>
              </div>
            </div>

            {/* What Happens Next */}
            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-6">
              <h3 className="font-semibold text-lg mb-6 text-purple-900 text-center">
                What Happens Next? ✨
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-purple-600 font-bold text-lg">1</span>
                  </div>
                  <h4 className="font-medium text-gray-900 mb-1">Instant Welcome</h4>
                  <p className="text-sm text-gray-600">Your AI coach greets you personally</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-purple-600 font-bold text-lg">2</span>
                  </div>
                  <h4 className="font-medium text-gray-900 mb-1">Personal Setup</h4>
                  <p className="text-sm text-gray-600">Share your goals and challenges</p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <span className="text-purple-600 font-bold text-lg">3</span>
                  </div>
                  <h4 className="font-medium text-gray-900 mb-1">Daily Coaching</h4>
                  <p className="text-sm text-gray-600">Personalized support begins</p>
                </div>
              </div>
            </div>

            {/* Support */}
            <div className="text-center text-sm text-gray-600 border-t pt-6">
              <p>Need help? Email us at <a href="mailto:support@positivitypush.com" className="text-blue-600 hover:underline font-medium">support@positivitypush.com</a></p>
              <div className="mt-4">
                <Link href="/">
                  <Button variant="outline" size="sm">
                    ← Back to Home
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function SuccessPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      </div>
    }>
      <SuccessPageContent />
    </Suspense>
  )
}