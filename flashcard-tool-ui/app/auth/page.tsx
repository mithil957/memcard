"use client";

import type React from "react";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { pb } from "@/lib/pocketbase";
import { useToast } from "@/hooks/use-toast";

export default function AuthPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState(""); // For registration
  const [isLoading, setIsLoading] = useState(false);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await pb.collection("users").authWithPassword(email, password);
      toast({
        title: "Signed In",
        description: "Welcome back!",
      });
      router.push("/actions");
    } catch (error: any) {
      toast({
        title: "Sign In Failed",
        description: error.message || "An unexpected error occurred.",
        variant: "destructive",
      });
      console.error("Sign In Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== passwordConfirm) {
      toast({
        title: "Registration Failed",
        description: "Passwords do not match.",
        variant: "destructive",
      });
      return;
    }
    setIsLoading(true);

    try {
      // Create the user
      await pb.collection("users").create({
        email,
        password,
        passwordConfirm,
      });

      // For now, login the user after a successful registration. Later, we will update
      // this so that an email with a code is sent the user's email and we can verify them
      await pb.collection("users").authWithPassword(email, password);

      toast({
        title: "Registration Successful",
        description: "You are now signed in.",
      });
      router.push("/actions");
    } catch (error: any) {
      let errorMessage = "An unexpected error occurred.";
      if (error.data && error.data.data) {
        const fieldErrors = Object.values(error.data.data).map(
          (err: any) => err.message,
        );
        if (fieldErrors.length > 0) {
          errorMessage = fieldErrors.join(" ");
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      toast({
        title: "Registration Failed",
        variant: "destructive",
      });
      console.error("Registration Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-2">
      <Card className="w-full max-w-md bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden">
        <Link
          href="/"
          className="flex items-center gap-0 mb-2 cursor-pointer pt-3 pl-2"
        >
          <Image
            src="/memcard_logo.png"
            alt="MemCard Logo"
            width={70}
            height={70}
          />
          <span className="font-mono text-4xl font-medium">MemCard</span>
        </Link>

        <div className="h-px w-full bg-[#C6D5EB] mb-6" />

        <Tabs defaultValue="signin" className="w-full pl-4 pr-4 pb-6">
          <TabsList className="grid w-full grid-cols-2 mb-6 h-auto rounded-full bg-[#D9D9D9] p-1">
            <TabsTrigger
              value="signin"
              className="font-sans font-medium text-lg rounded-full"
            >
              Sign In
            </TabsTrigger>
            <TabsTrigger
              value="register"
              className="font-sans font-medium text-lg rounded-full"
            >
              Register
            </TabsTrigger>
          </TabsList>

          <TabsContent value="signin">
            <form onSubmit={handleSignIn} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12 rounded-lg text-2xl md:text-2xl"
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12 rounded-lg text-2xl md:text-2xl"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12 rounded-xl text-2xl"
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign in"}
              </Button>
              <div className="text-right">
                <Link
                  href="#"
                  className="text-lg text-blue-600 hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
            </form>
          </TabsContent>

          <TabsContent value="register">
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-12 rounded-lg text-2xl md:text-2xl"
                />
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-12 rounded-lg text-2xl md:text-2xl"
                />
                <Input
                  type="password"
                  placeholder="Confirm Password" // New Field
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  required
                  className="h-12 rounded-lg text-2xl md:text-2xl"
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12 rounded-xl text-2xl"
                disabled={isLoading}
              >
                {isLoading ? "Registering..." : "Register"}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
