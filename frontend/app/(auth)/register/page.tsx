import AuthPlaceholder from "@/components/auth/auth-placeholder";

export default function RegisterPage() {
  return (
    <AuthPlaceholder
      heading="Create account"
      action="Create account"
      fields={[
        { label: "Name", type: "text" },
        { label: "Email", type: "email" },
        { label: "Password", type: "password" },
      ]}
    />
  );
}
