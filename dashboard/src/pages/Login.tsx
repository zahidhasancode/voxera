import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Shield, Mic, Zap, Plug } from "lucide-react";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/contexts/AuthContext";
import { ApiError } from "@/lib/api/client";
import { README_URL } from "@/projectLinks";

function signInErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if ([400, 401, 403, 422].includes(err.status)) {
      return "Sign-in failed. Check the email and password.";
    }
    return `Sign-in failed: the backend API answered with HTTP ${err.status}. Check that it is running locally.`;
  }
  return "Sign-in failed: the backend API could not be reached. Start it locally and try again.";
}

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { signIn, signInWithGoogle, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/app";
  const busy = isLoading || submitting;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signIn(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(signInErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGoogleSignIn() {
    setError(null);
    setSubmitting(true);
    try {
      await signInWithGoogle();
      navigate(from, { replace: true });
    } catch {
      setError("Google sign-in is not available: it is not configured on the backend.");
    } finally {
      setSubmitting(false);
    }
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
            Admin console for a voice-agent prototype
          </h2>
          <p className="mt-4 max-w-md text-muted-foreground">
            A user-interface prototype for the VOXERA real-time voice agent. It talks to the backend API, which you run on your own machine.
          </p>
          <ul className="mt-8 space-y-4">
            {[
              { icon: Zap, text: "Streaming speech-to-text, language model, and text-to-speech" },
              { icon: Mic, text: "Turn-taking and barge-in" },
              { icon: Plug, text: "Pluggable providers" },
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
        <p className="text-2xs text-muted-foreground">Built by MD Zahid Hasan</p>
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
          <h1 className="text-2xl font-semibold text-foreground">Sign in to the console</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            The console needs the backend API running locally; the hosted page has no backend, so sign-in does not work there.{" "}
            <a
              href={README_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-4 hover:text-foreground"
            >
              Setup instructions
            </a>
          </p>
          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {error && (
              <Alert variant="error" title="Could not sign in" onDismiss={() => setError(null)}>
                {error}
              </Alert>
            )}
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
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
            <Button type="submit" className="w-full" loading={busy}>
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
            disabled={busy}
            onClick={handleGoogleSignIn}
          >
            Sign in with Google
          </Button>
        </div>
      </div>
    </div>
  );
}
