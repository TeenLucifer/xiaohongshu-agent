import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import { useEffect } from "react";
import { Button } from "./ui/Button";

export interface LightboxImage {
  imageUrl: string;
  alt: string;
}

interface ImageLightboxProps {
  images: LightboxImage[];
  index: number;
  open: boolean;
  onClose: () => void;
  onIndexChange: (nextIndex: number) => void;
}

export function ImageLightbox({
  images,
  index,
  open,
  onClose,
  onIndexChange,
}: ImageLightboxProps): JSX.Element {
  const activeImage = images[index] ?? null;
  const hasMultipleImages = images.length > 1;

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    function handleKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        onClose();
        return;
      }

      if (!hasMultipleImages) {
        return;
      }

      if (event.key === "ArrowLeft") {
        onIndexChange(Math.max(0, index - 1));
      }
      if (event.key === "ArrowRight") {
        onIndexChange(Math.min(images.length - 1, index + 1));
      }
    }

    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [hasMultipleImages, images.length, index, onClose, onIndexChange, open]);

  return (
    <AnimatePresence>
      {open && activeImage ? (
        <motion.div
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/72 px-4 py-6"
          exit={{ opacity: 0 }}
          initial={{ opacity: 0 }}
          onClick={onClose}
          role="presentation"
          transition={{ duration: 0.18, ease: "easeOut" }}
        >
          <motion.div
            animate={{ opacity: 1, scale: 1, y: 0 }}
            aria-label="图片预览"
            aria-modal="true"
            className="relative w-full max-w-5xl"
            exit={{ opacity: 0, scale: 0.98, y: 10 }}
            initial={{ opacity: 0, scale: 0.98, y: 12 }}
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            transition={{ duration: 0.18, ease: "easeOut" }}
          >
            <div className="absolute right-0 top-0 z-10 flex items-center gap-2">
              {hasMultipleImages ? (
                <div className="rounded-full bg-slate-950/60 px-3 py-1 text-xs font-medium text-white">
                  {index + 1} / {images.length}
                </div>
              ) : null}
              <Button
                aria-label="关闭图片预览"
                className="bg-slate-950/60 text-white hover:bg-slate-950"
                onClick={onClose}
                size="icon"
                type="button"
                variant="ghost"
              >
                <X className="h-4 w-4" strokeWidth={1.8} />
              </Button>
            </div>

            <div className="flex items-center justify-center gap-4">
              {hasMultipleImages ? (
                <Button
                  aria-label="上一张预览图片"
                  className="bg-slate-950/60 text-white hover:bg-slate-950"
                  disabled={index === 0}
                  onClick={() => onIndexChange(Math.max(0, index - 1))}
                  size="icon"
                  type="button"
                  variant="ghost"
                >
                  <ChevronLeft className="h-5 w-5" />
                </Button>
              ) : null}

              <div className="max-h-[88vh] w-full overflow-hidden rounded-[28px] bg-slate-950/20 shadow-2xl">
                <img
                  alt={activeImage.alt}
                  className="max-h-[88vh] w-full object-contain"
                  src={activeImage.imageUrl}
                />
              </div>

              {hasMultipleImages ? (
                <Button
                  aria-label="下一张预览图片"
                  className="bg-slate-950/60 text-white hover:bg-slate-950"
                  disabled={index === images.length - 1}
                  onClick={() => onIndexChange(Math.min(images.length - 1, index + 1))}
                  size="icon"
                  type="button"
                  variant="ghost"
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>
              ) : null}
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
