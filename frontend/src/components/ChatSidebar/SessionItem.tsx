import { MessageSquare, Pencil, Trash2 } from 'lucide-react'
import { useState } from 'react'
import type { Session } from '../../types'

interface SessionItemProps {
  session: Session
  isActive: boolean
  onSelect: (id: string) => void
  onRename: (id: string, title: string) => void
  onDelete: (id: string) => void
}

export default function SessionItem({
  session,
  isActive,
  onSelect,
  onRename,
  onDelete,
}: SessionItemProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(session.title)

  const commitRename = () => {
    if (draft.trim() && draft.trim() !== session.title) {
      onRename(session.id, draft)
    }
    setEditing(false)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onSelect(session.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onSelect(session.id)
      }}
      className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isActive
          ? 'bg-slate-800 text-white'
          : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
      }`}
    >
      <MessageSquare className="w-4 h-4 shrink-0" />
      {editing ? (
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commitRename()
            if (e.key === 'Escape') {
              setDraft(session.title)
              setEditing(false)
            }
          }}
          onClick={(e) => e.stopPropagation()}
          className="flex-1 min-w-0 bg-slate-900 text-sm text-white rounded px-1.5 py-0.5 outline-none border border-blue-500/50"
        />
      ) : (
        <span className="flex-1 min-w-0 truncate text-sm">{session.title}</span>
      )}
      {!editing && (
        <span className="hidden group-hover:flex items-center gap-1 shrink-0">
          <button
            title="Rename"
            onClick={(e) => {
              e.stopPropagation()
              setDraft(session.title)
              setEditing(true)
            }}
            className="p-1 rounded hover:bg-slate-700 text-slate-500 hover:text-white"
          >
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button
            title="Delete"
            onClick={(e) => {
              e.stopPropagation()
              onDelete(session.id)
            }}
            className="p-1 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </span>
      )}
    </div>
  )
}
