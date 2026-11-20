import AuthPlaceholder from "@/components/auth/auth-placeholder";

export default function LoginPage() {
  return (
    <AuthPlaceholder
      heading="Log in"
      action="Log in"
      fields={[
        { label: "Email", type: "email" },
        { label: "Password", type: "password" },
      ]}
    />
  );
}
