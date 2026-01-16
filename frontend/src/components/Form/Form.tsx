import React from 'react';
import { useForm, UseFormProps, UseFormReturn, FieldError } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

interface FormProps<T extends z.ZodSchema>
  extends Omit<UseFormProps<z.infer<T>>, 'resolver'> {
  schema: T;
  onSubmit: (data: z.infer<T>) => void | Promise<void>;
  children: (methods: UseFormReturn<z.infer<T>>) => React.ReactNode;
  className?: string;
}

export function useVckForm<T extends z.ZodSchema>(
  props: UseFormProps<z.infer<T>> & { schema: T }
) {
  return useForm({
    resolver: zodResolver(props.schema),
    ...props,
  });
}

export function Form<T extends z.ZodSchema>({
  schema,
  onSubmit,
  children,
  className,
  ...formProps
}: FormProps<T>) {
  const methods = useForm({
    resolver: zodResolver(schema),
    ...formProps,
  });

  const handleSubmit = methods.handleSubmit(async (data) => {
    await onSubmit(data);
  });

  return (
    <form onSubmit={handleSubmit} className={className}>
      {children(methods)}
    </form>
  );
}

export function getFieldError(
  errors: Record<string, FieldError | undefined>,
  fieldName: string
): string | undefined {
  const error = errors[fieldName];
  return error?.message;
}

export function getFieldProps<T extends Record<string, unknown>>(
  name: keyof T,
  methods: UseFormReturn<T>
) {
  const error = methods.formState.errors[name] as FieldError | undefined;
  return {
    ...methods.register(name as string),
    error: error?.message,
  };
}
