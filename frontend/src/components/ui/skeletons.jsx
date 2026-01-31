import { Skeleton } from "./skeleton";
import { Card, CardContent, CardHeader } from "./card";

// Skeleton لبطاقة الإحصائيات
export const StatCardSkeleton = () => (
  <Card className="bg-slate-800 border-slate-700">
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-4 w-20 bg-slate-700" />
          <Skeleton className="h-8 w-16 bg-slate-700" />
        </div>
        <Skeleton className="h-10 w-10 rounded-full bg-slate-700" />
      </div>
    </CardContent>
  </Card>
);

// Skeleton لصف الجدول
export const TableRowSkeleton = ({ columns = 5 }) => (
  <tr className="border-b border-slate-700">
    {Array.from({ length: columns }).map((_, i) => (
      <td key={i} className="p-3">
        <Skeleton className="h-4 w-full bg-slate-700" />
      </td>
    ))}
  </tr>
);

// Skeleton للجدول كامل
export const TableSkeleton = ({ rows = 5, columns = 5 }) => (
  <div className="border border-slate-700 rounded-lg overflow-hidden">
    <div className="bg-slate-800 p-3">
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1 bg-slate-700" />
        ))}
      </div>
    </div>
    <div className="divide-y divide-slate-700">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-3 flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="h-4 flex-1 bg-slate-700" />
          ))}
        </div>
      ))}
    </div>
  </div>
);

// Skeleton للبطاقة
export const CardSkeleton = () => (
  <Card className="bg-slate-800 border-slate-700">
    <CardHeader>
      <Skeleton className="h-6 w-32 bg-slate-700" />
    </CardHeader>
    <CardContent className="space-y-3">
      <Skeleton className="h-4 w-full bg-slate-700" />
      <Skeleton className="h-4 w-3/4 bg-slate-700" />
      <Skeleton className="h-4 w-1/2 bg-slate-700" />
    </CardContent>
  </Card>
);

// Skeleton للقائمة
export const ListSkeleton = ({ items = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: items }).map((_, i) => (
      <div key={i} className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg">
        <Skeleton className="h-10 w-10 rounded-full bg-slate-700" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/3 bg-slate-700" />
          <Skeleton className="h-3 w-1/2 bg-slate-700" />
        </div>
      </div>
    ))}
  </div>
);

// Skeleton لصفحة Dashboard
export const DashboardSkeleton = () => (
  <div className="space-y-6">
    {/* Stats Row */}
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <StatCardSkeleton key={i} />
      ))}
    </div>
    
    {/* Content */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <CardSkeleton />
      <CardSkeleton />
    </div>
    
    {/* Table */}
    <TableSkeleton rows={5} columns={6} />
  </div>
);

// Skeleton للنموذج
export const FormSkeleton = () => (
  <div className="space-y-4">
    {Array.from({ length: 4 }).map((_, i) => (
      <div key={i} className="space-y-2">
        <Skeleton className="h-4 w-20 bg-slate-700" />
        <Skeleton className="h-10 w-full bg-slate-700 rounded-md" />
      </div>
    ))}
    <div className="flex gap-2 pt-4">
      <Skeleton className="h-10 w-24 bg-slate-700 rounded-md" />
      <Skeleton className="h-10 w-24 bg-emerald-900/50 rounded-md" />
    </div>
  </div>
);

export default {
  StatCardSkeleton,
  TableRowSkeleton,
  TableSkeleton,
  CardSkeleton,
  ListSkeleton,
  DashboardSkeleton,
  FormSkeleton
};
