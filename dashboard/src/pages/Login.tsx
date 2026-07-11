import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Shield, Mic, Zap, Lock } from "lucide-react";
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
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="hidden w-1/2 flex-col justify-between bg-background-subtle/60 p-12 lg:flex">
        <Link to="/" className="flex items-center gap-3 font-semibold text-foreground">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          VOXERA
        </Link>
        <div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground">
            Enterprise voice AI for customer support
          </h2>
          <p className="mt-4 max-w-md text-muted-foreground">
            Real-time streaming, natural barge-in, and sub-400ms latency — built for contact centers at scale.
          </p>
          <ul className="mt-8 space-y-4">
            {[
              { icon: Mic, text: "Full-duplex voice conversations" },
              { icon: Zap, text: "Streaming STT, LLM, and TTS" },
              { icon: Lock, text: "SOC 2 aligned security" },
            ].map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-foreground">
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-muted">
                  <Icon className="h-4 w-4 text-primary-muted-foreground" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-2xs text-muted-foreground">© {new Date().getFullYear()} VOXERA</p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm">
          <Link
            to="/"
            className="mb-8 inline-block text-sm text-muted-foreground hover:text-foreground lg:hidden"
          >
            ← Back to home
          </Link>
          <div className="mb-8 flex justify-center lg:hidden">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>
          <h1 className="text-2xl font-semibold text-foreground">Welcome back</h1>
          <p className="mt-1 text-sm text-muted-foreground">Sign in to your VOXERA account</p>
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
            <Button type="submit" className="w-full" loading={isLoading}>
              Sign in
            </Button>
          </form>
          <div className="mt-4 flex items-center gap-4">
            <span className="flex-1 border-t border-border" />
            <span className="text-2xs text-muted-foreground">or</span>
            <span className="flex-1 border-t border-border" />
          </div>
          <Button
            type="button"
            variant="outline"
            className="mt-4 w-full"
            disabled={isLoading}
            onClick={handleGoogleSignIn}
          >
            Sign in with Google
          </Button>
        </div>
      </div>
    </div>
  );
}
