import { X } from "lucide-react";
import { useState } from "react";
import type { GeneratedImageResult } from "../types/workspace";
import { ImageLightbox } from "./ImageLightbox";

export function ImageResultsPanel({
  results,
  onRemove,
}: {
  results: GeneratedImageResult[];
  onRemove?: (imageId: string) => void;
}): JSX.Element {
  const [activeImageIndex, setActiveImageIndex] = useState<number | null>(null);

  if (results.length === 0) {
    return <p className="text-sm text-slate-500">空状态</p>;
  }

  return (
    <>
      <div className="max-h-[200px] overflow-y-auto rounded-lg bg-slate-50 p-2">
        <div className="flex flex-wrap gap-2">
        {results.map((image, index) => (
          <div
            className="group relative h-16 w-16 cursor-grab overflow-hidden rounded-lg border border-slate-200 bg-white"
            draggable
            key={image.id}
            onDragStart={(event) => {
              event.dataTransfer.setData(
                "image",
                JSON.stringify({
                  id: image.id,
                  sourceType: "generated",
                  imageUrl: image.imageUrl,
                  imagePath: image.imagePath,
                  alt: image.alt,
                })
              );
              event.dataTransfer.effectAllowed = "copy";
            }}
          >
            <button className="block h-full w-full" onClick={() => setActiveImageIndex(index)} type="button">
              <img
                alt={image.alt}
                className="h-full w-full cursor-zoom-in object-cover"
                draggable={false}
                src={image.imageUrl}
              />
            </button>
              {onRemove ? (
                <button
                  className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-slate-900/60 text-white opacity-0 transition-opacity hover:bg-slate-900 group-hover:opacity-100"
                  onClick={(event) => {
                    event.stopPropagation();
                    onRemove(image.id);
                  }}
                  type="button"
                >
                  <X className="h-3 w-3" />
                </button>
              ) : null}
          </div>
        ))}
        </div>
      </div>

      <ImageLightbox
        images={results.map((image) => ({
          imageUrl: image.imageUrl,
          alt: image.alt,
        }))}
        index={activeImageIndex ?? 0}
        onClose={() => setActiveImageIndex(null)}
        onIndexChange={setActiveImageIndex}
        open={activeImageIndex !== null}
      />
    </>
  );
}
