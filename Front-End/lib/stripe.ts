// Stripe integration utilities for Positivity Push

export type PlanType = "3-month" | "6-month"

export interface PlanDetails {
  id: PlanType
  name: string
  displayName: string
  price: string
  originalPrice?: string
  description: string
  stripeLink: string | undefined
  isPopular?: boolean
}

// Get Stripe payment link based on plan type
export function getStripeLink(planType: PlanType): string | undefined {
  switch (planType) {
    case "3-month":
      return process.env.NEXT_PUBLIC_STRIPE_LINK_3_MONTH
    case "6-month":
      return process.env.NEXT_PUBLIC_STRIPE_LINK_6_MONTH
    default:
      return undefined
  }
}

// Get plan details
export function getPlanDetails(planType: PlanType): PlanDetails {
  const baseDetails = {
    "3-month": {
      id: "3-month" as const,
      name: "3-Month Plan",
      displayName: "STARTER",
      price: "€28.99",
      description: "€9.72/month",
      isPopular: false,
    },
    "6-month": {
      id: "6-month" as const,
      name: "6-Month Plan",
      displayName: "THRIVE", 
      price: "€34.99",
      originalPrice: "€58.32",
      description: "€5.83/month ≈ €0.19/day",
      isPopular: true,
    },
  }

  const plan = baseDetails[planType]
  return {
    ...plan,
    stripeLink: getStripeLink(planType),
  }
}

// Handle Stripe checkout redirect
export function redirectToStripe(planType: PlanType): void {
  const stripeLink = getStripeLink(planType)
  
  if (!stripeLink || stripeLink.includes('placeholder')) {
    alert(`Payment system is not yet configured for ${getPlanDetails(planType).name}. This is a demo version.`)
    return
  }
  
  // Redirect to Stripe Checkout
  window.location.href = stripeLink
}

// Check if Stripe is properly configured
export function isStripeConfigured(): boolean {
  const links = [
    process.env.NEXT_PUBLIC_STRIPE_LINK_3_MONTH,
    process.env.NEXT_PUBLIC_STRIPE_LINK_6_MONTH,
  ]
  
  return links.every(link => link && !link.includes('placeholder'))
}