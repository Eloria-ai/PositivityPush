"use client"

import { Suspense, useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { QRCodeSVG } from "qrcode.react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, MessageCircle, Smartphone, Copy, Check } from "lucide-react"
import Link from "next/link"

function SuccessPageContent() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session_id")
  const [copied, setCopied] = useState(false)
  
  // TODO: Replace with actual WhatsApp business number from environment
  const whatsappNumber = process.env.NEXT_PUBLIC_WA_BUSINESS_NUMBER || "1234567890"
  const activationMessage = `POSITIVITY-PUSH START ${sessionId || "DEMO"}`
  const whatsappUrl = `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(activationMessage)}`

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(activationMessage)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy text: ", err)
    }
  }

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
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">
            Payment Successful! 🎉
          </CardTitle>
          <CardDescription className="text-lg">
            Welcome to Positivity Push! Now let's activate your personal AI coach on WhatsApp.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-8">
          {/* Step-by-step instructions */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-blue-600" />
              Activate Your AI Coach in 2 Simple Steps:
            </h3>
            
            <div className="space-y-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  1
                </div>
                <div>
                  <p className="font-medium">Click the WhatsApp button below or scan the QR code</p>
                  <p className="text-sm text-gray-600">This will open WhatsApp with your activation message pre-filled</p>
                </div>
              </div>
              
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  2
                </div>
                <div>
                  <p className="font-medium">Tap "Send" in WhatsApp</p>
                  <p className="text-sm text-gray-600">Your AI coach will immediately welcome you and start learning about your goals!</p>
                </div>
              </div>
            </div>
          </div>

          {/* WhatsApp activation section */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* QR Code for mobile */}
            <div className="text-center">
              <h4 className="font-semibold mb-3 flex items-center justify-center gap-2">
                <Smartphone className="w-4 h-4" />
                Scan with Your Phone
              </h4>
              <div className="bg-white p-4 rounded-lg border-2 border-dashed border-gray-300 inline-block">
                <QRCodeSVG 
                  value={whatsappUrl}
                  size={150}
                  level="M"
                  includeMargin={true}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Open your camera app and point it at this QR code
              </p>
            </div>

            {/* Direct button for desktop */}
            <div className="text-center">
              <h4 className="font-semibold mb-3 flex items-center justify-center gap-2">
                <MessageCircle className="w-4 h-4" />
                Click to Open WhatsApp
              </h4>
              <div className="space-y-4">
                <a href={whatsappUrl} target="_blank" rel="noopener noreferrer">
                  <Button size="lg" className="w-full bg-green-600 hover:bg-green-700 text-white">
                    <MessageCircle className="w-5 h-5 mr-2" />
                    Activate AI Coach
                  </Button>
                </a>
                
                {/* Copy activation message */}
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-xs text-gray-600 mb-2">Activation Message:</p>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 text-sm bg-white p-2 rounded border text-left">
                      {activationMessage}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={copyToClipboard}
                      className="flex-shrink-0"
                    >
                      {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    You can copy this message and paste it manually in WhatsApp if needed
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* What happens next */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg p-6">
            <h3 className="font-semibold text-lg mb-4 text-purple-900">
              What Happens Next? ✨
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
              <div>
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-purple-600 font-bold">1</span>
                </div>
                <p className="text-sm font-medium">Instant Welcome</p>
                <p className="text-xs text-gray-600">Your AI coach greets you</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-purple-600 font-bold">2</span>
                </div>
                <p className="text-sm font-medium">Personal Setup</p>
                <p className="text-xs text-gray-600">Share your goals & challenges</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                  <span className="text-purple-600 font-bold">3</span>
                </div>
                <p className="text-sm font-medium">Daily Coaching</p>
                <p className="text-xs text-gray-600">Personalized support begins</p>
              </div>
            </div>
          </div>

          {/* Troubleshooting */}
          <div className="text-center text-sm text-gray-600">
            <p>Having trouble? Make sure you have WhatsApp installed on your device.</p>
            <p className="mt-1">
              Need help? Email us at{" "}
              <a href="mailto:support@positivitypush.com" className="text-blue-600 hover:underline">
                support@positivitypush.com
              </a>
            </p>
          </div>

          {/* Back to home link */}
          <div className="text-center pt-4 border-t">
            <Link href="/">
              <Button variant="outline">
                Return to Home Page
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>
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