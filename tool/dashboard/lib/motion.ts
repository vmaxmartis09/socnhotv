const seen = new Set<string>();
const pending = new Set<string>();

/**
 * Quy tắc animation: cái đã hiện rồi thì không chạy lại hiệu ứng xuất hiện khi mở cái khác / quay lại.
 * Dùng cho `initial` của framer-motion: lần đầu thấy `key` trả về `initial`, các lần sau trả về `false` (hiện ngay).
 * Ổn định qua các lần render lặp lại và hydration: máy chủ luôn trả `initial`; trình duyệt chỉ đánh dấu "đã thấy" sau 400ms.
 */
export function enterOnce<T extends object>(key: string, initial: T): T | false {
  if (typeof window === "undefined") return initial;
  if (seen.has(key)) return false;
  if (!pending.has(key)) {
    pending.add(key);
    window.setTimeout(() => seen.add(key), 400);
  }
  return initial;
}
