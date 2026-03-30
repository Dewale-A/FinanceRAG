import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL || "http://35.171.2.221";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const apiKey = request.headers.get("X-API-Key") || "";

    const headers: Record<string, string> = {};
    if (apiKey) {
      headers["X-API-Key"] = apiKey;
    }

    const res = await fetch(`${API_URL}/ingest/upload`, {
      method: "POST",
      headers,
      body: formData,
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    return NextResponse.json(
      { error: "Failed to upload" },
      { status: 502 }
    );
  }
}
