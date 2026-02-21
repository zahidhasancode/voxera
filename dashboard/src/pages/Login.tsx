import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Shield } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/contexts/AuthContext";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { signIn, signInWithGoogle, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/app";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await signIn(email, password);
    navigate(from, { replace: true });
  }

  async function handleGoogleSignIn() {
    await signInWithGoogle();
    navigate(from, { replace: true });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 inline-block text-sm text-muted-foreground hover:text-foreground">
          ← Back to home
        </Link>
        <div className="mb-8 flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
            <Shield className="h-6 w-6 text-primary-foreground" />
          </div>
        </div>
        <h1 className="text-center text-xl font-semibold text-foreground">
          VOXERA
        </h1>
        <p className="mt-1 text-center text-sm text-muted-foreground">
          Sign in to your account
        </p>
        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <Input
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            required
          />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Signing in…" : "Sign in with email"}
          </Button>
        </form>
        <div className="mt-4 flex items-center gap-4">
          <span className="flex-1 border-t border-border" />
          <span className="text-2xs text-muted-foreground">or</span>
          <span className="flex-1 border-t border-border" />
        </div>
        <Button
          type="button"
          variant="secondary"
          className="mt-4 w-full"
          disabled={isLoading}
          onClick={handleGoogleSignIn}
        >
          Sign in with Google
        </Button>
        <p className="mt-6 text-center text-xs text-muted-foreground">
          Demo: any email/password or Google will sign you in. Wire to your auth backend for production.
        </p>
      </div>
    </div>
  );
}
