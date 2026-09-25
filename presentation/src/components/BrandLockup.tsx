import type { BrandConfig } from '../types'

export function BrandLockup({ brand, compact = false }: { brand: BrandConfig; compact?: boolean }) {
  return (
    <div className={`brand-lockup ${compact ? 'brand-lockup-compact' : ''}`} aria-label={brand.attribution}>
      <img src={brand.primary.logo} alt={brand.primary.alt} />
      <span aria-hidden="true">×</span>
      <img src={brand.partner.logo} alt={brand.partner.alt} />
    </div>
  )
}
