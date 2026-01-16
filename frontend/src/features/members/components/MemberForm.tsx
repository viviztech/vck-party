/**
 * Member Form Component
 * Form for creating and editing members using react-hook-form and zod
 */

import React, { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Textarea } from '@/components/Form/Textarea';
import { Button } from '@/components/Form/Button';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import type { Member, MemberCreate, MemberUpdate } from '@/services/membersService';

const memberSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().optional(),
  first_name_ta: z.string().optional(),
  last_name_ta: z.string().optional(),
  phone: z.string().min(10, 'Valid phone number is required'),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  address_line1: z.string().optional(),
  address_line2: z.string().optional(),
  city: z.string().optional(),
  district: z.string().optional(),
  constituency: z.string().optional(),
  ward: z.string().optional(),
  state: z.string().optional(),
  pincode: z.string().optional(),
  voter_id: z.string().optional(),
  blood_group: z.string().optional(),
  education: z.string().optional(),
  occupation: z.string().optional(),
  organization: z.string().optional(),
  membership_type: z.string().optional(),
});

type MemberFormData = z.infer<typeof memberSchema>;

interface MemberFormProps {
  member?: Member;
  onSubmit: (data: MemberCreate | MemberUpdate) => Promise<void>;
  onCancel: () => void;
}

export function MemberForm({ member, onSubmit, onCancel }: MemberFormProps) {
  const isEditing = !!member;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
    control,
  } = useForm<MemberFormData>({
    resolver: zodResolver(memberSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      phone: '',
      email: '',
      gender: '',
      membership_type: 'regular',
    },
  });

  useEffect(() => {
    if (member) {
      reset({
        first_name: member.first_name,
        last_name: member.last_name || '',
        first_name_ta: member.first_name_ta || '',
        last_name_ta: member.last_name_ta || '',
        phone: member.phone,
        email: member.email || '',
        date_of_birth: member.date_of_birth || '',
        gender: member.gender || '',
        address_line1: member.address_line1 || '',
        address_line2: member.address_line2 || '',
        city: member.city || '',
        district: member.district || '',
        constituency: member.constituency || '',
        ward: member.ward || '',
        state: member.state || '',
        pincode: member.pincode || '',
        voter_id: member.voter_id || '',
        blood_group: member.blood_group || '',
        education: member.education || '',
        occupation: member.occupation || '',
        organization: member.organization || '',
        membership_type: member.membership_type || 'regular',
      });
    }
  }, [member, reset]);

  const onFormSubmit = async (data: MemberFormData) => {
    const submitData = isEditing
      ? { ...data, id: member.id } as MemberUpdate
      : data as MemberCreate;
    await onSubmit(submitData);
  };

  const genderOptions = [
    { value: 'male', label: 'Male' },
    { value: 'female', label: 'Female' },
    { value: 'other', label: 'Other' },
  ];

  const bloodGroupOptions = [
    { value: '', label: 'Select' },
    { value: 'A+', label: 'A+' },
    { value: 'A-', label: 'A-' },
    { value: 'B+', label: 'B+' },
    { value: 'B-', label: 'B-' },
    { value: 'AB+', label: 'AB+' },
    { value: 'AB-', label: 'AB-' },
    { value: 'O+', label: 'O+' },
    { value: 'O-', label: 'O-' },
  ];

  const membershipTypeOptions = [
    { value: 'regular', label: 'Regular' },
    { value: 'life', label: 'Life Member' },
    { value: 'honorary', label: 'Honorary' },
    { value: 'founder', label: 'Founder' },
  ];

  return (
    <form onSubmit={handleSubmit(onFormSubmit)}>
      <Card>
        <CardHeader title={isEditing ? 'Edit Member' : 'New Member'} />
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="First Name *" {...register('first_name')} error={errors.first_name?.message} />
                <Input label="Last Name" {...register('last_name')} error={errors.last_name?.message} />
                <Input label="Phone *" {...register('phone')} error={errors.phone?.message} />
                <Input label="Email" type="email" {...register('email')} error={errors.email?.message} />
                <Input label="Date of Birth" type="date" {...register('date_of_birth')} error={errors.date_of_birth?.message} />
                <Controller name="gender" control={control} render={({ field }) => (
                  <Select label="Gender" options={genderOptions} {...field} onChange={(value) => field.onChange(value)} />
                )} />
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Address</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2"><Textarea label="Address Line 1" {...register('address_line1')} rows={2} /></div>
                <div className="md:col-span-2"><Textarea label="Address Line 2" {...register('address_line2')} rows={2} /></div>
                <Input label="City" {...register('city')} />
                <Input label="District" {...register('district')} />
                <Input label="Constituency" {...register('constituency')} />
                <Input label="Ward" {...register('ward')} />
                <Input label="State" {...register('state')} />
                <Input label="Pincode" {...register('pincode')} />
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Additional Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input label="Voter ID" {...register('voter_id')} />
                <Controller name="blood_group" control={control} render={({ field }) => (
                  <Select label="Blood Group" options={bloodGroupOptions} {...field} onChange={(value) => field.onChange(value)} />
                )} />
                <Input label="Education" {...register('education')} />
                <Input label="Occupation" {...register('occupation')} />
                <Input label="Organization" {...register('organization')} />
                <Controller name="membership_type" control={control} render={({ field }) => (
                  <Select label="Membership Type" options={membershipTypeOptions} {...field} onChange={(value) => field.onChange(value)} />
                )} />
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-end space-x-3">
          <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={isSubmitting}>{isEditing ? 'Update Member' : 'Create Member'}</Button>
        </CardFooter>
      </Card>
    </form>
  );
}

export default MemberForm;
