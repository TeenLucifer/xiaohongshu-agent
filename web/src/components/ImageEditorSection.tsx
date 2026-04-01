import { X } from "lucide-react";
import { useCallback, useState } from "react";
import { cn } from "../lib/cn";
import type { EditorImage, MaterialImage } from "../types/workspace";
import { ImageLightbox, type LightboxImage } from "./ImageLightbox";

interface ImageEditorSectionProps {
  materialImages: MaterialImage[];
  editorImages: EditorImage[];
  onEditorImagesChange: (images: EditorImage[]) => void;
}

export function ImageEditorSection({
  materialImages,
  editorImages,
  onEditorImagesChange,
}: ImageEditorSectionProps): JSX.Element {
  const [dragOverEditor, setDragOverEditor] = useState(false);
  const [lightboxImages, setLightboxImages] = useState<LightboxImage[]>([]);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  // 处理拖拽开始
  const handleDragStart = useCallback(
    (e: React.DragEvent, image: MaterialImage) => {
      e.dataTransfer.setData("image", JSON.stringify(image));
      e.dataTransfer.effectAllowed = "copy";
    },
    []
  );

  // 处理拖拽进入编辑区
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
    setDragOverEditor(true);
  }, []);

  // 处理拖拽离开编辑区
  const handleDragLeave = useCallback(() => {
    setDragOverEditor(false);
  }, []);

  // 处理放置
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOverEditor(false);

      const imageData = e.dataTransfer.getData("image");
      if (!imageData) return;

      try {
        const image = JSON.parse(imageData) as
          | MaterialImage
          | {
              id: string;
              sourceType: "generated";
              imageUrl: string;
              imagePath: string;
              alt: string;
            };
        const nextId = `editor-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        let newEditorImage: EditorImage;
        if ("sourceType" in image && image.sourceType === "generated") {
          newEditorImage = {
            id: nextId,
            order: editorImages.length + 1,
            sourceType: "generated",
            sourceGeneratedImageId: image.id,
            imageUrl: image.imageUrl,
            imagePath: image.imagePath,
            alt: image.alt,
          };
        } else if ("postId" in image) {
          newEditorImage = {
            id: nextId,
            order: editorImages.length + 1,
            sourceType: "material",
            sourcePostId: image.postId,
            sourceImageId: image.id,
            imageUrl: image.imageUrl,
            imagePath: image.imagePath,
            alt: image.alt,
          };
        } else {
          return;
        }
        onEditorImagesChange([...editorImages, newEditorImage]);
      } catch {
        // 忽略解析错误
      }
    },
    [editorImages, onEditorImagesChange]
  );

  // 移除编辑区图片
  const handleRemoveImage = useCallback(
    (imageId: string) => {
      const newImages = editorImages
        .filter((img) => img.id !== imageId)
        .map((img, index) => ({ ...img, order: index + 1 }));
      onEditorImagesChange(newImages);
    },
    [editorImages, onEditorImagesChange]
  );

  const openLightbox = useCallback((images: LightboxImage[], index: number) => {
    setLightboxImages(images);
    setLightboxIndex(index);
  }, []);

  const materialLightboxImages = materialImages.map((image) => ({
    imageUrl: image.imageUrl,
    alt: image.alt,
  }));

  const editorLightboxImages = editorImages.map((image) => ({
    imageUrl: image.imageUrl,
    alt: image.alt,
  }));

  return (
    <>
      <div className="flex flex-col gap-3">
        {/* 素材区 */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-500">素材图片 ({materialImages.length})</p>
          {materialImages.length === 0 ? (
            <p className="text-xs text-slate-400">搜索帖子后，图片会出现在这里</p>
          ) : (
            <div className="max-h-[200px] overflow-y-auto rounded-lg bg-slate-50 p-2">
              <div className="flex flex-wrap gap-2">
                {materialImages.map((image, index) => (
                  <div
                    className="group relative h-16 w-16 cursor-grab overflow-hidden rounded-lg border border-slate-200 bg-white"
                    draggable
                    key={image.id}
                    onClick={() => openLightbox(materialLightboxImages, index)}
                    onDragStart={(e) => handleDragStart(e, image)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openLightbox(materialLightboxImages, index);
                      }
                    }}
                  >
                    <img
                      alt={image.alt}
                      className="h-full w-full cursor-zoom-in object-cover"
                      draggable={false}
                      src={image.imageUrl}
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-slate-900/60 px-1 py-0.5 text-[8px] text-white opacity-0 transition-opacity group-hover:opacity-100">
                      {image.postTitle.slice(0, 8)}...
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 编辑区 */}
        <div>
          <p className="mb-2 text-xs font-medium text-slate-500">编辑区 ({editorImages.length})</p>
          <div
            className={cn(
              "min-h-[80px] rounded-lg border-2 border-dashed p-2 transition-colors",
              dragOverEditor
                ? "border-blue-400 bg-blue-50"
                : editorImages.length === 0
                  ? "border-slate-200 bg-slate-50"
                  : "border-slate-200 bg-white"
            )}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            {editorImages.length === 0 ? (
              <p className="flex h-[48px] items-center justify-center text-xs text-slate-400">
                拖拽素材图片到这里
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {editorImages.map((image, index) => (
                  <div
                    className="group relative h-16 w-16 overflow-hidden rounded-lg border border-slate-200 bg-white"
                    key={image.id}
                    onClick={() => openLightbox(editorLightboxImages, index)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        openLightbox(editorLightboxImages, index);
                      }
                    }}
                  >
                    <img
                      alt={image.alt}
                      className="h-full w-full cursor-zoom-in object-cover"
                      draggable={false}
                      src={image.imageUrl}
                    />
                    {/* 编号 */}
                    <span className="absolute left-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-blue-600 text-[10px] font-bold text-white">
                      {image.order}
                    </span>
                    {/* 删除按钮 */}
                    <button
                      className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-slate-900/60 text-white opacity-0 transition-opacity hover:bg-slate-900 group-hover:opacity-100"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleRemoveImage(image.id);
                      }}
                      type="button"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <ImageLightbox
        images={lightboxImages}
        index={lightboxIndex ?? 0}
        onClose={() => setLightboxIndex(null)}
        onIndexChange={setLightboxIndex}
        open={lightboxIndex !== null && lightboxImages.length > 0}
      />
    </>
  );
}
