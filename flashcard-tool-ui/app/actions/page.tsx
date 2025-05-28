"use client";

import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { FilePlus2, ListChecks } from "lucide-react";

export default function ActionPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen w-full bg-gradient-to-tr from-[#51A4EE] to-[#214DCE] flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl bg-[#FAF9F7] rounded-3xl shadow-lg overflow-hidden">
        <div className="p-3 flex">
          {" "}
          {/* Centered logo */}
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

        <div className="pt-8 px-8 pb-12 flex flex-col items-center gap-6">
          {" "}
          {/* Centered content */}
          <div className="text-center space-y-2.5">
            {" "}
            {/* Centered text */}
            <h1 className="text-4xl font-semibold tracking-normal">
              Choose Your Action
            </h1>
            <p className="text-black text-xl font-extralight">
              Select whether you'd like to create new flashcards or view the
              status of existing jobs.
            </p>
          </div>
          <div className="w-full max-w-md space-y-4 pt-4">
            {" "}
            {/* Max width for buttons and spacing */}
            <Button
              className="w-full text-xl tracking-tight bg-blue-600 hover:bg-blue-700 text-white px-5 py-6 h-auto flex items-center justify-center gap-2"
              onClick={() => router.push("/wizard")}
            >
              <FilePlus2 className="h-6 w-6" />
              Request Flashcards
            </Button>
            <Button
              variant="outline" // Different variant for visual distinction
              className="w-full text-xl tracking-tight px-5 py-6 h-auto border-blue-600 text-blue-600 hover:bg-blue-50 hover:text-blue-700 flex items-center justify-center gap-2"
              onClick={() => router.push("/jobstat")}
            >
              <ListChecks className="h-6 w-6" />
              View Jobs
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
