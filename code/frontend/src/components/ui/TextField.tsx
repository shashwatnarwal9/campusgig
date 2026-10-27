import { type InputHTMLAttributes, useId } from 'react';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  hint?: string;
}

export function TextField({ label, error, hint, id, className = '', ...rest }: TextFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        {label}
      </label>
      <input
        {...rest}
        id={inputId}
        className={`field__input${error ? ' field__input--error' : ''} ${className}`.trim()}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : hint ? hintId : undefined}
      />
      {error ? (
        <p className="field__error" id={errorId} role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="field__hint" id={hintId}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
