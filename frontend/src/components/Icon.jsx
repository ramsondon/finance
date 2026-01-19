import {
  BarChart3,
  CreditCard,
  RotateCw,
  Folder,
  Settings,
  Zap,
  TrendingUp,
  TrendingDown,
  Search,
  Download,
  Lock,
  AlertCircle,
  Upload,
  Loader,
  Calendar,
  Clock,
  ArrowLeftRight,
  DollarSign,
  CheckCircle,
  PieChart,
} from 'lucide-react'

// Icon mapping for consistent usage across the app
export const ICON_MAP = {
  // Navigation
  dashboard: BarChart3,
  transactions: CreditCard,
  recurring: RotateCw,
  categories: Folder,
  rules: Settings,
  insights: Zap,

  // Finance indicators
  income: TrendingUp,
  expense: TrendingDown,
  transfer: ArrowLeftRight,
  balance: DollarSign,
  cashFlow: BarChart3,

  // UI elements
  search: Search,
  refresh: RotateCw,
  upload: Upload,
  import: Download,
  security: Lock,
  warning: AlertCircle,
  loading: Loader,
  calendar: Calendar,
  clock: Clock,
  checkCircle: CheckCircle,
  pieChart: PieChart,
}

export function Icon({ name, size = 24, className = '' }) {
  const IconComponent = ICON_MAP[name]
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found in ICON_MAP`)
    return null
  }
  return <IconComponent size={size} className={className} />
}

