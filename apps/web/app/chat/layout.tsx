import { AppLayout } from "@/components/app-layout";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AppLayout>{children}</AppLayout>;
}
