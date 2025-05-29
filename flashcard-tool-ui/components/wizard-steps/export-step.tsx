"use client";

import { useState } from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { CheckCircle, Copy, Download } from "lucide-react"; // Added Download icon
import { toast } from "@/components/ui/use-toast";

interface ExportStepProps {
  flashcards: Array<{ question: string; answer: string; id: string }>;
}

const escapeCsvField = (field: string): string => {
  if (field === null || field === undefined) {
    return "";
  }
  const stringField = String(field);
  if (stringField.includes(",") || stringField.includes("\n") || stringField.includes('"')) {
    return `"${stringField.replace(/"/g, '""')}"`;
  }
  return stringField;
};

const formatForObsidian = (
  flashcards: Array<{ question: string; answer: string; id: string }>,
) => {
  return flashcards
    .map((card) => `${card.question}::${card.answer}`)
    .join("\n\n");
};

const formatRowForAnkiCsv = (card: { question: string; answer: string }): string => {
  return `${escapeCsvField(card.question)},${escapeCsvField(card.answer)}`;
};

export default function ExportStep({ flashcards }: ExportStepProps) {
  const [exportFormat, setExportFormat] = useState<"obsidian" | "anki">(
    "obsidian",
  );
  const [copied, setCopied] = useState(false);

  const handleCopyToClipboard = async () => {
    // For Obsidian, clipboard is the primary action
    if (exportFormat !== "obsidian") {
        toast({
            title: "Action Not Applicable",
            description: "Copy to clipboard is configured for Obsidian format in this setup.",
            variant: "default"
        });
        return;
    }

    const formattedText = formatForObsidian(flashcards);

    try {
      await navigator.clipboard.writeText(formattedText);
      setCopied(true);
      toast({
        title: "Copied to clipboard",
        description: "Flashcards copied in Obsidian format.",
      });

      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      toast({
        title: "Failed to copy",
        description: "Could not copy to clipboard. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleDownloadAnkiCsv = () => {
    if (exportFormat !== "anki") return;

    const csvContent = flashcards.map(formatRowForAnkiCsv).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", "anki_flashcards.csv");
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url); 

    toast({
      title: "Download Started",
      description: "Anki CSV file download has started.",
    });
  };

  return (
    <div className="py-4 flex flex-col h-full">
      <h2 className="text-3xl font-semibold mb-1">Export</h2>
      <p className="text-base font-light text-gray-600 mb-8">
        Choose export format to save to your favorite tool.
      </p>

      <RadioGroup
        defaultValue="obsidian"
        onValueChange={(value: "obsidian" | "anki") => setExportFormat(value)}
        className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6"
      >
        {/* Obsidian Option */}
        <Label
          htmlFor="obsidian"
          className={`flex flex-col items-center justify-center p-6 border-2 rounded-lg cursor-pointer transition-all
                ${exportFormat === "obsidian" ? "border-blue-600 ring-2 ring-blue-[#214DCE] bg-blue-50" : "border-gray-300 hover:border-gray-400"}`}
        >
          <Image
            src="/obsidian-icon.png"
            alt="Obsidian Logo"
            width={64}
            height={64}
            className="mb-3"
          />
          <div className="flex items-center">
            <RadioGroupItem value="obsidian" id="obsidian" className="mr-2" />
            <span className="font-medium text-lg">Obsidian</span>
          </div>
        </Label>

        <Label
          htmlFor="anki"
          className={`flex flex-col items-center justify-center p-6 border-2 rounded-lg cursor-pointer transition-all
                ${exportFormat === "anki" ? "border-blue-600 ring-2 ring-blue-[#214DCE] bg-blue-50" : "border-gray-300 hover:border-gray-400"}`}
        >
          <Image
            src="/anki-icon.png"
            alt="Anki Logo"
            width={64}
            height={64}
            className="mb-3"
          />
          <div className="flex items-center">
            <RadioGroupItem value="anki" id="anki" className="mr-2" />
            <span className="font-medium text-lg">Anki</span>
          </div>
        </Label>
      </RadioGroup>

      <div className="flex flex-col space-y-3">
        {exportFormat === "obsidian" && (
          <Button
            onClick={handleCopyToClipboard}
            className="w-full text-lg py-6"
            variant="outline"
          >
            {copied ? (
              <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
            ) : (
              <Copy className="mr-2 h-5 w-5" />
            )}
            {copied ? "Copied for Obsidian!" : "Copy for Obsidian"}
          </Button>
        )}

        {exportFormat === "anki" && (
          <Button
            onClick={handleDownloadAnkiCsv}
            className="w-full text-lg py-6"
            variant="outline" // Or any other variant you prefer
          >
            <Download className="mr-2 h-5 w-5" />
            Download Anki CSV
          </Button>
        )}
      </div>
    </div>
  );
}