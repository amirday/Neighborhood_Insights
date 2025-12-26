import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-bold uppercase tracking-wide transition-standard disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none font-['Outfit']",
  {
    variants: {
      variant: {
        default: "brutal-button",
        destructive:
          "bg-[var(--color-bright-coral)] text-[var(--color-surface)] border-[3px] border-[var(--color-border)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0_var(--color-border)] active:translate-x-0 active:translate-y-0 active:shadow-[2px_2px_0_var(--color-border)]",
        outline:
          "bg-transparent text-[var(--color-text-primary)] border-[3px] border-[var(--color-border)] hover:bg-[var(--color-border)] hover:text-[var(--color-surface)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[4px_4px_0_var(--color-bright-coral)]",
        secondary:
          "bg-[var(--color-sky-blue)] text-[var(--color-surface)] border-[3px] border-[var(--color-border)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0_var(--color-border)] active:translate-x-0 active:translate-y-0 active:shadow-[2px_2px_0_var(--color-border)]",
        ghost:
          "hover:bg-[var(--color-border-light)] text-[var(--color-text-primary)]",
        link: "text-[var(--color-sky-blue)] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 py-2.5",
        sm: "h-9 gap-1.5 px-4 py-2",
        lg: "h-13 px-7 py-3.5",
        icon: "size-11",
        "icon-sm": "size-9",
        "icon-lg": "size-13",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
