import Image from "next/image"
import { Menu } from "lucide-react"

export function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Mobile Menu */}
        <div className="md:hidden">
          <Menu className="w-6 h-6 text-gray-600" />
        </div>

        {/* Logo - Centered */}
        <div className="flex items-center flex-1 justify-center md:justify-start">
          <Image
            src="/positivity-push-logo.png"
            alt="Positivity Push"
            width={180}
            height={60}
            priority
            className="h-10 w-auto"
          />
        </div>

        {/* Empty space for balance on mobile */}
        <div className="md:hidden w-6"></div>
      </div>
    </header>
  )
}
