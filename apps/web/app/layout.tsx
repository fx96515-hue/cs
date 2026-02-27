import "./globals.css";
import AppShell from "./components/AppShell";
import QueryProvider from "./components/QueryProvider";

export const metadata = {
  title: "CoffeeStudio",
  description: "CoffeeStudio Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="de">
      <body>
        <QueryProvider>
          <AppShell>{children}</AppShell>
        </QueryProvider>
      </body>
    </html>
  );
}
