import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

/**
 * Khung tạm cho các trang chưa code nghiệp vụ.
 * `todo` liệt kê phần sẽ dựng ở giai đoạn code thật.
 */
export function PagePlaceholder({ title, description, todo, children }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-4">
        {todo && todo.length > 0 && (
          <div className="bg-muted/40 rounded-md border border-dashed p-4">
            <p className="text-muted-foreground mb-2 text-sm font-medium">
              Sẽ dựng ở bước code nghiệp vụ:
            </p>
            <ul className="text-muted-foreground list-inside list-disc space-y-1 text-sm">
              {todo.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {children}
      </CardContent>
    </Card>
  );
}
