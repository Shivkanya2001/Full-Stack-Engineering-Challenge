import clsx from "clsx";

export function Card({
  children,
  className,
  title,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
}) {
  return (
    <div className={clsx("rounded-xl border border-border bg-card/80 p-6 shadow-xl backdrop-blur", className)}>
      {title && <h2 className="mb-4 text-lg font-semibold text-foreground">{title}</h2>}
      {children}
    </div>
  );
}
