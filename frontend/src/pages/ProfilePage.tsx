import { motion } from 'framer-motion';
import { type ChangeEvent, useEffect, useRef, useState } from 'react';

import { Alert } from '../components/ui/Alert';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { useAuth } from '../hooks/useAuth';
import { useProfile } from '../hooks/useProfile';
import { formatDate } from '../lib/format';
import { errorMessage, mediaUrl } from '../services/apiClient';
import { profileApi } from '../services/profileApi';

const MAX_BIO = 1000;

export function ProfilePage() {
  const { user } = useAuth();
  const { profile, loading, error, setProfile } = useProfile();

  const [bio, setBio] = useState('');
  const [savingBio, setSavingBio] = useState(false);
  const [uploading, setUploading] = useState<'avatar' | 'resume' | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);

  const avatarInput = useRef<HTMLInputElement>(null);
  const resumeInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setBio(profile?.bio ?? '');
  }, [profile?.bio]);

  const flash = (message: string) => {
    setNotice(message);
    window.setTimeout(() => setNotice(null), 4000);
  };

  const saveBio = async () => {
    setProblem(null);
    setSavingBio(true);
    try {
      setProfile(await profileApi.updateBio(bio));
      flash('Profile saved.');
    } catch (caught) {
      setProblem(errorMessage(caught));
    } finally {
      setSavingBio(false);
    }
  };

  const pickFile =
    (kind: 'avatar' | 'resume') => async (event: ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      // Reset immediately so re-picking the same file still fires onChange.
      event.target.value = '';
      if (!file) return;

      setProblem(null);
      setUploading(kind);
      try {
        setProfile(
          kind === 'avatar'
            ? await profileApi.uploadAvatar(file)
            : await profileApi.uploadResume(file),
        );
        flash(kind === 'avatar' ? 'Profile picture updated.' : 'Resume uploaded.');
      } catch (caught) {
        setProblem(errorMessage(caught));
      } finally {
        setUploading(null);
      }
    };

  if (loading && !profile) {
    return (
      <div className="dashboard__loading">
        <Spinner label="Loading your profile" />
      </div>
    );
  }

  if (error && !profile) return <Alert tone="error">{error}</Alert>;
  if (!profile) return null;

  const initials = (profile.roll_no ?? 'CG').slice(-2);
  const avatar = mediaUrl(profile.avatar_url);
  const resume = mediaUrl(profile.resume_url);

  return (
    <div className="profile">
      <header className="dashboard__header">
        <div>
          <h1 className="dashboard__title">
            Your <em>Profile</em>
          </h1>
          <p className="dashboard__welcome">
            This is what other students see when you apply to their gigs.
          </p>
        </div>
      </header>

      {notice ? <Alert tone="success">{notice}</Alert> : null}
      {problem ? <Alert tone="error">{problem}</Alert> : null}

      <div className="profile__grid">
        <motion.section
          className="panel profile__identity"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24 }}
        >
          <div className="avatar-block">
            {avatar ? (
              <img className="avatar-block__image" src={avatar} alt="Your profile picture" />
            ) : (
              <span className="avatar-block__initials" aria-hidden="true">
                {initials}
              </span>
            )}
          </div>

          <div className="avatar-block__actions">
            <input
              ref={avatarInput}
              className="sr-only"
              type="file"
              accept="image/png,image/jpeg,image/gif,image/webp"
              onChange={pickFile('avatar')}
            />
            <Button
              variant="secondary"
              onClick={() => avatarInput.current?.click()}
              loading={uploading === 'avatar'}
            >
              {avatar ? 'Change picture' : 'Upload picture'}
            </Button>
            <p className="field__hint">JPEG, PNG, GIF or WEBP. Up to 2 MB.</p>
          </div>

          <h2 className="profile__name">{profile.roll_no}</h2>
          <p className="profile__meta">
            {profile.dept} &middot; Batch {profile.batch}
          </p>
        </motion.section>

        <motion.section
          className="panel"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, delay: 0.05 }}
        >
          <h2 className="panel__title">About you</h2>
          <div className="field">
            <label className="field__label" htmlFor="profile-bio">
              Short description
            </label>
            <textarea
              id="profile-bio"
              className="field__input field__textarea"
              rows={5}
              maxLength={MAX_BIO}
              placeholder="What you are good at, what kind of work you want, when you are free."
              value={bio}
              onChange={(event) => setBio(event.target.value)}
            />
            <p className="field__hint">
              {bio.length}/{MAX_BIO}
            </p>
          </div>
          <Button onClick={saveBio} loading={savingBio}>
            Save
          </Button>
        </motion.section>

        <motion.section
          className="panel"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, delay: 0.1 }}
        >
          <h2 className="panel__title">Resume</h2>
          {resume ? (
            <p className="profile__resume">
              <a href={resume} target="_blank" rel="noreferrer">
                View your uploaded resume (PDF)
              </a>
            </p>
          ) : (
            <p className="field__hint">No resume uploaded yet.</p>
          )}
          <input
            ref={resumeInput}
            className="sr-only"
            type="file"
            accept="application/pdf"
            onChange={pickFile('resume')}
          />
          <Button
            variant="secondary"
            onClick={() => resumeInput.current?.click()}
            loading={uploading === 'resume'}
          >
            {resume ? 'Replace resume' : 'Upload resume'}
          </Button>
          <p className="field__hint">PDF only. Up to 5 MB.</p>
        </motion.section>

        <motion.section
          className="panel"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.24, delay: 0.15 }}
        >
          <h2 className="panel__title">Account details</h2>
          <dl className="detail-list">
            <div>
              <dt>Institutional email</dt>
              <dd>{profile.email}</dd>
            </div>
            <div>
              <dt>Roll number</dt>
              <dd>{profile.roll_no}</dd>
            </div>
            <div>
              <dt>Department</dt>
              <dd>{profile.dept}</dd>
            </div>
            <div>
              <dt>Batch</dt>
              <dd>{profile.batch}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{profile.role === 'ADMIN' ? 'Administrator' : 'Student'}</dd>
            </div>
            <div>
              <dt>Member since</dt>
              <dd>{formatDate(profile.created_at ?? user?.created_at ?? '')}</dd>
            </div>
          </dl>
          <p className="field__hint">
            These came from signup and cannot be edited yet.
          </p>
        </motion.section>
      </div>
    </div>
  );
}
