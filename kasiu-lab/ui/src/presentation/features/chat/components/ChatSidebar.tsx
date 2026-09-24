import React, { useState } from "react";
import {
  ChevronRight,
  Edit2,
  FilePlus,
  FolderPlus,
  GripVertical,
  MessageSquare,
  Search,
} from "lucide-react";
import { ActiveEntity, FSItem } from "../../views/types";
import { Divider, SectionLabel } from "../../views/ui-helpers";
import { THEME_COLORS, renderItemIcon } from "./shared";

export interface ChatSidebarProps {
  width: number;
  isOpen: boolean;
  isDragging: boolean;
  activeEntity: ActiveEntity;
  fsItems: FSItem[];
  draggedItemId: string | null;
  onResizeStart: (e: React.MouseEvent) => void;
  onSelectEntity: (entity: ActiveEntity) => void;
  onDragStart: (e: React.DragEvent, id: string) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDrop: (e: React.DragEvent, targetId: string | null) => void;
  onCreateFolder: () => void;
  onCreateNotebook: () => void;
  onEditEntity?: (item: FSItem) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  width,
  isOpen,
  isDragging,
  activeEntity,
  fsItems,
  draggedItemId,
  onResizeStart,
  onSelectEntity,
  onDragStart,
  onDragOver,
  onDrop,
  onCreateFolder,
  onCreateNotebook,
  onEditEntity,
}) => {
  const [query, setQuery] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(["fadena", "fadena_1ano", "fadena_1ano_2cuat", "roadmap", "roadmap_fase0"])
  );

  const toggleFolder = (folderId: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  const renderChildren = (parentId: string, depth = 0): React.ReactNode => {
    const children = fsItems.filter((i) => i.parentId === parentId);
    if (!children.length) return null;

    return children.map((child) => {
      const cleanName = child.name.replace(".nb", "");
      const isSelected = activeEntity.id === child.id;
      const isFolder = child.type === "folder";
      const isExpanded = expandedFolders.has(child.id);
      const colorConfig = THEME_COLORS[child.color || (isFolder ? "amber" : "blue")] || THEME_COLORS.amber;

      return (
        <div key={child.id} className="space-y-1">
          <div
            draggable
            onDragStart={(e) => onDragStart(e, child.id)}
            onDragOver={onDragOver}
            onDrop={(e) => onDrop(e, child.type === "folder" ? child.id : parentId)}
            onClick={() => {
              onSelectEntity({
                id: child.id,
                name: isFolder ? child.name : cleanName,
                type: child.type,
              });
              if (isFolder && !isExpanded) {
                toggleFolder(child.id);
              }
            }}
            className={[
              "flex items-center gap-2 py-1.5 px-2 rounded-[12px] cursor-pointer transition text-xs font-mono group border",
              isSelected
                ? `${colorConfig.bg} ${colorConfig.border} ${colorConfig.text} font-semibold shadow-xs`
                : draggedItemId === child.id
                ? "opacity-35 border-transparent"
                : "text-white/70 hover:text-white hover:bg-white/[0.04] border-transparent",
            ].join(" ")}
            style={{ marginLeft: depth * 12 }}
          >
            <div className="w-4 h-4 flex items-center justify-center shrink-0">
              <GripVertical className="w-3.5 h-3.5 opacity-30 group-hover:opacity-60" />
            </div>
            {isFolder ? (
              <button
                type="button"
                onClick={(e) => toggleFolder(child.id, e)}
                className="w-4 h-4 flex items-center justify-center shrink-0 hover:text-white"
                title={isExpanded ? "Colapsar carpeta" : "Expandir carpeta"}
              >
                <ChevronRight
                  className={`w-3.5 h-3.5 transition-transform duration-150 ${
                    isExpanded ? "rotate-90 text-white/90" : "text-white/40"
                  }`}
                />
              </button>
            ) : (
              <span className="w-4 shrink-0" />
            )}
            <span className={colorConfig.text}>
              {renderItemIcon(child.icon, isFolder, isExpanded, "w-4 h-4 shrink-0")}
            </span>
            <span className="truncate flex-1 min-w-0">{cleanName}</span>
            <div className="flex items-center gap-1 shrink-0">
              {onEditEntity && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEditEntity(child);
                  }}
                  className={`w-5 h-5 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition ${
                    isSelected ? "hover:bg-white/20 text-current" : "hover:bg-white/10 text-white/60 hover:text-white"
                  }`}
                  title="Personalizar nombre, icono y color"
                >
                  <Edit2 className="w-3 h-3" />
                </button>
              )}
              {isSelected && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${colorConfig.dot} ${colorConfig.glow}`} />}
            </div>
          </div>

          {isFolder && isExpanded && (
            <div className="ml-3.5 border-l border-white/[0.07] pl-1.5 space-y-1">
              {renderChildren(child.id, depth + 1)}
            </div>
          )}
        </div>
      );
    });
  };

  return (
    <>
      <aside
        style={{
          width: isOpen ? width : 0,
          opacity: isOpen ? 1 : 0,
          transition: isDragging
            ? "none"
            : "width 240ms cubic-bezier(0.16, 1, 0.3, 1), opacity 180ms ease-out",
        }}
        className="h-full shrink-0 bg-[#0a0a0c] border-r border-white/[0.07] flex flex-col overflow-hidden select-none"
      >
        <div className="px-5 py-4 shrink-0 min-w-[280px]">
          <div className="flex items-center justify-between">
            <SectionLabel eyebrow="navegación" title="Árbol curricular" />
            <div className="flex items-center gap-1.5">
              <button
                onClick={onCreateNotebook}
                className="w-8 h-8 rounded-[11px] border border-white/[0.08] bg-white/[0.03] hover:bg-white hover:text-black flex items-center justify-center transition text-white"
                title="Nuevo Cuaderno"
              >
                <FilePlus className="w-4 h-4" />
              </button>
              <button
                onClick={onCreateFolder}
                className="w-8 h-8 rounded-[11px] border border-white/[0.08] bg-white/[0.03] hover:bg-white hover:text-black flex items-center justify-center transition text-white"
                title="Nueva Carpeta"
              >
                <FolderPlus className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="mt-3.5 h-10 rounded-[13px] bg-[#101012] border border-white/[0.08] flex items-center px-3 gap-2.5">
            <Search className="w-4 h-4 text-white/30" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar rama o materia..."
              className="flex-1 bg-transparent outline-none text-xs font-mono text-white placeholder:text-white/25"
            />
          </div>
        </div>

        <Divider />

        <div
          className="flex-1 overflow-y-auto k-scroll px-3 py-3 min-w-[280px]"
          onDragOver={onDragOver}
          onDrop={(e) => onDrop(e, null)}
        >
          {/* ACCESO PERMANENTE: CHAT GENERAL */}
          <div
            onClick={() => {
              onSelectEntity({
                id: "root_global",
                name: "Chat General",
                type: "root",
              });
            }}
            className={[
              "flex items-center gap-2.5 py-2 px-2.5 rounded-[13px] cursor-pointer transition text-xs font-mono group border mb-3 select-none",
              activeEntity.id === "root_global"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300 font-semibold shadow-xs"
                : "bg-white/[0.02] border-white/[0.06] text-white/70 hover:text-white hover:border-white/20 hover:bg-white/[0.04]",
            ].join(" ")}
          >
            <MessageSquare className="w-4 h-4 text-emerald-400 shrink-0" />
            <div className="flex-1 truncate flex items-center justify-between">
              <span className="font-semibold tracking-wide text-[11px] truncate">Chat General</span>
              <span className="text-[8.5px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono uppercase font-bold shrink-0 ml-1">
                GLOBAL
              </span>
            </div>
            {activeEntity.id === "root_global" && (
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#10b981] shrink-0" />
            )}
          </div>

          {fsItems
            .filter((i) => i.parentId === null)
            .filter((i) => i.name.toLowerCase().includes(query.toLowerCase()))
            .map((root) => {
              const isSelected = activeEntity.id === root.id;
              const isFolder = root.type === "folder";
              const isExpanded = expandedFolders.has(root.id);
              const colorConfig = THEME_COLORS[root.color || (isFolder ? "amber" : "blue")] || THEME_COLORS.amber;

              return (
                <div
                  key={root.id}
                  draggable
                  onDragStart={(e) => onDragStart(e, root.id)}
                  className="mb-2"
                >
                  <div 
                    onClick={() => {
                      onSelectEntity({ id: root.id, name: root.name, type: root.type });
                      if (isFolder && !isExpanded) toggleFolder(root.id);
                    }}
                    className={[
                      "flex items-center justify-between px-2.5 py-2 rounded-[12px] cursor-pointer transition group border",
                      isSelected
                        ? `${colorConfig.bg} ${colorConfig.border} ${colorConfig.text} font-semibold shadow-xs`
                        : "text-white/80 hover:bg-white/[0.04] border-transparent"
                    ].join(" ")}
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <div className="w-4 h-4 flex items-center justify-center shrink-0">
                        <GripVertical className="w-3.5 h-3.5 opacity-25 group-hover:opacity-60" />
                      </div>
                      {isFolder ? (
                        <button
                          type="button"
                          onClick={(e) => toggleFolder(root.id, e)}
                          className="w-4 h-4 flex items-center justify-center shrink-0 hover:text-white"
                          title={isExpanded ? "Colapsar carpeta" : "Expandir carpeta"}
                        >
                          <ChevronRight
                            className={`w-3.5 h-3.5 transition-transform duration-150 ${
                              isExpanded ? "rotate-90 text-current" : "opacity-40"
                            }`}
                          />
                        </button>
                      ) : (
                        <span className="w-4 shrink-0" />
                      )}
                      <span className={colorConfig.text}>
                        {renderItemIcon(root.icon, isFolder, isExpanded, "w-4 h-4 shrink-0")}
                      </span>
                      <span className="text-xs font-mono font-semibold uppercase tracking-wider truncate flex-1 min-w-0">
                        {root.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {onEditEntity && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onEditEntity(root);
                          }}
                          className={`w-5 h-5 rounded flex items-center justify-center opacity-0 group-hover:opacity-100 transition ${
                            isSelected ? "hover:bg-white/20 text-current" : "hover:bg-white/10 text-white/60 hover:text-white"
                          }`}
                          title="Personalizar nombre, icono y color"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                      )}
                      {isSelected && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${colorConfig.dot} ${colorConfig.glow}`} />}
                    </div>
                  </div>

                  {isFolder && isExpanded && (
                    <div className="ml-3.5 border-l border-white/[0.07] pl-1.5 mt-1 space-y-1">
                      {renderChildren(root.id)}
                    </div>
                  )}
                </div>
              );
            })}
        </div>

        <div className="border-t border-white/[0.08] bg-black/40 py-2 px-3 text-[11px] font-mono text-white/40 flex justify-between items-center shrink-0 min-w-[280px]">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/80 shadow-[0_0_6px_#34d399]" />
            <span>DnD Activo</span>
          </div>
          <span className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] text-[10px] text-white/50 font-mono">
            {fsItems.length} elementos
          </span>
        </div>
      </aside>

      {isOpen && (
        <div
          onMouseDown={onResizeStart}
          className={[
            "group w-[6px] shrink-0 cursor-col-resize flex items-center justify-center transition-colors select-none",
            isDragging ? "bg-amber-500/10" : "bg-transparent hover:bg-white/[0.03]",
          ].join(" ")}
          title="Arrastrar para redimensionar Árbol (P1)"
        >
          <div
            className={[
              "w-[2px] rounded-full transition-all duration-150",
              isDragging
                ? "bg-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.8)] h-20"
                : "bg-white/[0.12] group-hover:bg-white/[0.5] h-14 group-hover:h-18",
            ].join(" ")}
          />
        </div>
      )}
    </>
  );
};

export const CurriculumRail = ChatSidebar;
export default ChatSidebar;
