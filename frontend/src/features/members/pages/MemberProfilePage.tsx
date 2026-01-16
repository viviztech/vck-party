/**
 * Member Profile Page
 * Page for managing a member's extended profile
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { PageHeader } from '@/components/Layout/PageHeader';
import { Card, CardContent, CardFooter } from '@/components/DataDisplay/Card';
import { Tabs } from '@/components/DataDisplay/Tabs';
import { Input } from '@/components/Form/Input';
import { Select } from '@/components/Form/Select';
import { Button } from '@/components/Form/Button';
import { Checkbox } from '@/components/Form/Checkbox';
import { membersService, MemberProfile, MemberProfileUpdate } from '@/services/membersService';
import { Save, User, Heart, Shield, Briefcase } from 'lucide-react';
import { Spinner } from '@/components/Feedback/Spinner';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const profileSchema = z.object({
  mother_tongue: z.string().optional(),
  religion: z.string().optional(),
  caste_category: z.string().optional(),
  nationality: z.string().optional(),
  facebook_url: z.string().url().optional().or(z.literal('')),
  twitter_url: z.string().url().optional().or(z.literal('')),
  instagram_url: z.string().url().optional().or(z.literal('')),
  linkedin_url: z.string().url().optional().or(z.literal('')),
  emergency_contact_name: z.string().optional(),
  emergency_contact_phone: z.string().optional(),
  emergency_contact_relationship: z.string().optional(),
  communication_preference: z.string().optional(),
  language_preference: z.string().optional(),
  previous_party_affiliation: z.string().optional(),
  joined_from_which_party: z.string().optional(),
  political_influence_level: z.string().optional(),
  volunteer_availability: z.string().optional(),
  max_travel_distance_km: z.number().optional(),
  hobbies_interests: z.string().optional(),
  achievements_recognitions: z.string().optional(),
  photo_consent: z.boolean().optional(),
  data_sharing_consent: z.boolean().optional(),
});

type ProfileFormData = z.infer<typeof profileSchema>;

export function MemberProfilePage() {
  const { id } = useParams<{ id: string }>();
  const [profile, setProfile] = useState<MemberProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');

  const { register, handleSubmit, control, formState: { errors }, reset } = useForm<ProfileFormData>({
    resolver: zodResolver(profileSchema),
  });

  useEffect(() => {
    if (!id) return;

    const fetchProfile = async () => {
      try {
        const profileData = await membersService.getMemberProfile(id);
        setProfile(profileData);
        reset({
          mother_tongue: profileData.mother_tongue,
          religion: profileData.religion,
          caste_category: profileData.caste_category,
          nationality: profileData.nationality,
          facebook_url: profileData.facebook_url,
          twitter_url: profileData.twitter_url,
          instagram_url: profileData.instagram_url,
          linkedin_url: profileData.linkedin_url,
          emergency_contact_name: profileData.emergency_contact_name,
          emergency_contact_phone: profileData.emergency_contact_phone,
          emergency_contact_relationship: profileData.emergency_contact_relationship,
          communication_preference: profileData.communication_preference,
          language_preference: profileData.language_preference,
          previous_party_affiliation: profileData.previous_party_affiliation,
          joined_from_which_party: profileData.joined_from_which_party,
          political_influence_level: profileData.political_influence_level,
          volunteer_availability: profileData.volunteer_availability,
          hobbies_interests: profileData.hobbies_interests,
          achievements_recognitions: profileData.achievements_recognitions,
          photo_consent: profileData.photo_consent,
          data_sharing_consent: profileData.data_sharing_consent,
          max_travel_distance_km: profileData.max_travel_distance_km,
        });
      } catch (error) {
        console.error('Failed to fetch profile:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [id, reset]);

  const onSubmit = async (data: ProfileFormData) => {
    if (!id) return;
    setSaving(true);
    try {
      const updateData: MemberProfileUpdate = data;
      const updatedProfile = await membersService.updateMemberProfile(id, updateData);
      setProfile(updatedProfile);
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  const tabs = [
    { key: 'personal', label: 'Personal', icon: <User size={16} /> },
    { key: 'emergency', label: 'Emergency Contact', icon: <Heart size={16} /> },
    { key: 'political', label: 'Political', icon: <Briefcase size={16} /> },
    { key: 'consent', label: 'Consent', icon: <Shield size={16} /> },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Member Profile"
        description="Manage extended profile information"
        breadcrumbs={[
          { label: 'Members', href: '/members' },
          { label: id || '', href: `/members/${id}` },
          { label: 'Profile' },
        ]}
      />

      <Card padding="none">
        <div className="p-4 border-b border-gray-200">
          <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />
        </div>

        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="p-6">
            {activeTab === 'personal' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input label="Mother Tongue" {...register('mother_tongue')} error={errors.mother_tongue?.message} />
                  <Input label="Religion" {...register('religion')} error={errors.religion?.message} />
                  <Input label="Caste Category" {...register('caste_category')} error={errors.caste_category?.message} />
                  <Input label="Nationality" {...register('nationality')} error={errors.nationality?.message} />
                </div>

                <h3 className="font-semibold text-gray-900">Social Links</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input label="Facebook URL" type="url" {...register('facebook_url')} error={errors.facebook_url?.message} />
                  <Input label="Twitter URL" type="url" {...register('twitter_url')} error={errors.twitter_url?.message} />
                  <Input label="Instagram URL" type="url" {...register('instagram_url')} error={errors.instagram_url?.message} />
                  <Input label="LinkedIn URL" type="url" {...register('linkedin_url')} error={errors.linkedin_url?.message} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input label="Hobbies & Interests" {...register('hobbies_interests')} error={errors.hobbies_interests?.message} />
                  <Input label="Achievements & Recognitions" {...register('achievements_recognitions')} error={errors.achievements_recognitions?.message} />
                </div>
              </div>
            )}

            {activeTab === 'emergency' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input label="Emergency Contact Name" {...register('emergency_contact_name')} error={errors.emergency_contact_name?.message} />
                  <Input label="Emergency Contact Phone" {...register('emergency_contact_phone')} error={errors.emergency_contact_phone?.message} />
                  <Input label="Relationship" {...register('emergency_contact_relationship')} error={errors.emergency_contact_relationship?.message} />
                </div>
              </div>
            )}

            {activeTab === 'political' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Input label="Previous Party Affiliation" {...register('previous_party_affiliation')} error={errors.previous_party_affiliation?.message} />
                  <Input label="Joined From Which Party" {...register('joined_from_which_party')} error={errors.joined_from_which_party?.message} />
                  <Controller
                    name="political_influence_level"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Political Influence Level"
                        options={[
                          { value: 'low', label: 'Low' },
                          { value: 'medium', label: 'Medium' },
                          { value: 'high', label: 'High' },
                        ]}
                        {...field}
                        onChange={(value) => field.onChange(value)}
                      />
                    )}
                  />
                  <Controller
                    name="volunteer_availability"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Volunteer Availability"
                        options={[
                          { value: 'weekdays', label: 'Weekdays' },
                          { value: 'weekends', label: 'Weekends' },
                          { value: 'flexible', label: 'Flexible' },
                          { value: 'full_time', label: 'Full Time' },
                        ]}
                        {...field}
                        onChange={(value) => field.onChange(value)}
                      />
                    )}
                  />
                  <Input label="Max Travel Distance (km)" type="number" {...register('max_travel_distance_km', { valueAsNumber: true })} error={errors.max_travel_distance_km?.message} />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Controller
                    name="communication_preference"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Communication Preference"
                        options={[
                          { value: 'phone', label: 'Phone' },
                          { value: 'email', label: 'Email' },
                          { value: 'whatsapp', label: 'WhatsApp' },
                          { value: 'sms', label: 'SMS' },
                        ]}
                        {...field}
                        onChange={(value) => field.onChange(value)}
                      />
                    )}
                  />
                  <Controller
                    name="language_preference"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Language Preference"
                        options={[
                          { value: 'ta', label: 'Tamil' },
                          { value: 'en', label: 'English' },
                          { value: 'hi', label: 'Hindi' },
                        ]}
                        {...field}
                        onChange={(value) => field.onChange(value)}
                      />
                    )}
                  />
                </div>
              </div>
            )}

            {activeTab === 'consent' && (
              <div className="space-y-6">
                <Checkbox {...register('photo_consent')}>I consent to having my photo used for organizational purposes</Checkbox>
                <Checkbox {...register('data_sharing_consent')}>I consent to having my data shared within the organization</Checkbox>
              </div>
            )}
          </div>

          <CardFooter className="flex justify-end space-x-3">
            <Button type="button" variant="outline" onClick={() => history.back()}>Cancel</Button>
            <Button type="submit" loading={saving} leftIcon={<Save size={16} />}>Save Profile</Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

export default MemberProfilePage;
