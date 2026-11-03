export interface ShortcutGroup {
  title: string;
  items: { keys: string[]; label: string }[];
}

/** Nguồn duy nhất cho danh sách phím tắt; màn "Phím tắt" đọc từ đây. Thêm phím tắt mới thì thêm vào đây. */
export const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: "Chung",
    items: [
      { keys: ["Esc"], label: "Đóng xem trước, rồi thu gọn panel bên phải" },
      { keys: ["Ctrl", "B"], label: "Mở/đóng panel bên phải" },
      { keys: ["?"], label: "Mở danh sách phím tắt" },
      { keys: ["Alt", "1…7"], label: "Chuyển nhanh giữa 7 panel (Dự án, Nhân vật, Chat, Lịch đăng, Hàng đợi, Node, Phím tắt)" },
      { keys: ["Enter"], label: "Xác nhận trong hộp xác nhận" },
    ],
  },
  {
    title: "Danh sách",
    items: [
      { keys: ["Click"], label: "Chọn và xem trước (mở rộng sang trái)" },
      { keys: ["Double-click"], label: "Mở / vào: dự án → vào Studio, kịch bản → đọc đầy đủ" },
    ],
  },
  {
    title: "Công cụ Studio (thanh bên trái)",
    items: [
      { keys: ["N"], label: "Thêm node" },
      { keys: ["V"], label: "Chọn" },
      { keys: ["H"], label: "Kéo canvas" },
      { keys: ["["], label: "Thêm bước trước node đang chọn" },
      { keys: ["]"], label: "Thêm bước sau node đang chọn" },
      { keys: ["Ctrl", "D"], label: "Nhân bản node" },
      { keys: ["Delete"], label: "Xóa node / đường nối" },
      { keys: ["G"], label: "Sắp xếp nhóm" },
      { keys: ["Ctrl", "Z"], label: "Hoàn tác" },
      { keys: ["Ctrl", "Shift", "Z"], label: "Làm lại" },
      { keys: ["S"], label: "Bật/tắt bắt dính lưới" },
    ],
  },
  {
    title: "Canvas Studio",
    items: [
      { keys: ["Enter"], label: "Chạy node đang chọn" },
      { keys: ["Ctrl", "C"], label: "Sao chép node" },
      { keys: ["Ctrl", "V"], label: "Dán node" },
    ],
  },
];

/** Phím tắt hiện cạnh tên công cụ trong tooltip của thanh công cụ Studio. */
export const TOOL_KEYS = {
  add: "N",
  select: "V",
  pan: "H",
  stepBefore: "[",
  stepAfter: "]",
  duplicate: "Ctrl+D",
  delete: "Del",
  group: "G",
  undo: "Ctrl+Z",
  redo: "Ctrl+Shift+Z",
  snap: "S",
} as const;
