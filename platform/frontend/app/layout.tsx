import type { Metadata } from "next";
import "@fontsource/vazirmatn/400.css";
import "@fontsource/vazirmatn/600.css";
import "@fontsource/vazirmatn/800.css";
import "./styles.css";
export const metadata: Metadata = {
  title: "کارما | سامانه یکپارچه تجارت صنعتی",
  description: "کاتالوگ استاندارد پیچ و مهره و سامانه مدیریت کارما",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl">
      <body>{children}</body>
    </html>
  );
}
