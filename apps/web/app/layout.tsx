import './globals.css';

export const metadata = { title: "Learning Space", description: "Personal knowledge management" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  );
}