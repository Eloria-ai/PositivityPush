import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { cn } from "@/lib/utils"

// Set up the Inter font with next/font
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans", // Use the CSS variable convention for shadcn/ui
})

export const metadata: Metadata = {
  title: "Positivity Push",
  description: "Feel Happier, Stay Grateful, Hit Your Goals",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      {/* Apply the font class to the body */}
      <body className={cn("min-h-screen bg-white font-sans antialiased", inter.variable)}>{children}</body>
    </html>
  )
}
