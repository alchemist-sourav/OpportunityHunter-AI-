import ProfileEditor from "@/components/profile/profile-editor";

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-10">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-indigo-600">Your workspace</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">Your profile</h1>
        <p className="mt-2 text-slate-600">Set your skills and preferences to improve opportunity matching.</p>
      </div>
      <ProfileEditor />
    </div>
  );
}
