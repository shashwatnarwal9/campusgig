import { type SelectHTMLAttributes, useId } from 'react';

interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Option[];
}

export function SelectField({ label, options, id, className = '', ...rest }: SelectFieldProps) {
  const generatedId = useId();
  const selectId = id ?? generatedId;

  return (
    <div className="field">
      <label className="field__label" htmlFor={selectId}>
        {label}
      </label>
      <select {...rest} id={selectId} className={`field__input ${className}`.trim()}>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
