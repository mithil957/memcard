"use client";

import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";

export default function HeroPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden">
        <div className="p-3 flex justify-between items-center">
          <div className="flex items-center gap-0">
            <Image
              src="/memcard_logo.png"
              alt="MemCard Logo"
              width={70}
              height={70}
            />
            <span className="font-mono text-4xl font-medium">MemCard</span>
          </div>
        </div>

        <div className="h-px w-full bg-[#C6D5EB]" />

        <div className="pt-8 px-8 pb-12 flex flex-col md:flex-row items-center gap-4">
          <div className="flex-1 space-y-2.5">
            <h1 className="text-5xl font-semibold tracking-normal">
              PDFs into Flashcards
            </h1>
            <p className="text-black text-3xl font-extralight">
              A clean, minimal utility to turn PDFs into flashcards to shorten
              your learning loop.
            </p>
            <div className="pt-4">
              <Button
                className="text-2xl tracking-tight bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 h-auto"
                onClick={() => router.push("/auth")}
              >
                Get started
              </Button>
            </div>
          </div>
          <div className="flex-shrink-0">
            <Image
              src="/hero_page_graphic.png"
              alt="Flashcards Illustration"
              width={200}
              height={200}
              className="object-contain"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
