import { LoginForm } from "@/components/login-form";

export default function LoginPage() {
  return (
    <section className="login-page">
      <div className="login-card">
        <p className="eyebrow">Pathos</p>
        <h1>Welcome back.</h1>
        <p className="lead">Sign in to review PR opportunities and their scoring evidence.</p>
        <LoginForm />
      </div>
    </section>
  );
}
