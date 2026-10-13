import React, { useCallback, useRef } from 'react'
import { MAX_FILE_SIZE_MB, SUPPORTED_FILE_EXTENSIONS } from '@/services/api'

interface FileUploadButtonProps {
  onSelect: (file: File) => void
  disabled?: boolean
  busy?: boolean
}

/**
 * Button that opens the file picker and hands the chosen file to `onSelect`.
 *
 * The `<input type="file">` is kept hidden and driven by the button so the
 * control can be styled like the rest of the action bar; its value is cleared
 * after every pick so selecting the same file twice still fires a change event.
 */
export const FileUploadButton: React.FC<FileUploadButtonProps> = ({
  onSelect,
  disabled = false,
  busy = false,
}) => {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      e.target.value = ''
      if (file) onSelect(file)
    },
    [onSelect],
  )

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept={SUPPORTED_FILE_EXTENSIONS.join(',')}
        onChange={handleChange}
        className="hidden"
        aria-hidden="true"
        tabIndex={-1}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        title={
          `Поддерживаются ${SUPPORTED_FILE_EXTENSIONS.join(', ')} ` +
          `— до ${MAX_FILE_SIZE_MB} МБ`
        }
        className="
          inline-flex items-center gap-2 px-5 py-2.5 rounded-xl
          border border-gray-200 text-gray-600 font-medium text-sm
          hover:bg-gray-50 hover:border-gray-300
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors duration-150
          focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-1
        "
      >
        <span className="text-base leading-none">{busy ? '⏳' : '📎'}</span>
        {busy ? 'Обработка файла…' : 'Загрузить файл'}
      </button>
    </>
  )
}
