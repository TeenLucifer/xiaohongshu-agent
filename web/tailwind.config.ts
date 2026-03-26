import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"PingFang SC"', '"Noto Sans SC"', '"Microsoft YaHei"', "system-ui", "sans-serif"]
      },
      boxShadow: {
        surface: "0 10px 30px rgba(15, 23, 42, 0.06)",
        floating: "0 24px 48px rgba(15, 23, 42, 0.14)"
      }
    }
  }
} satisfies Config;
