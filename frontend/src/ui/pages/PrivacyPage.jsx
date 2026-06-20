export default function PrivacyPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="font-display text-3xl font-bold text-ink mb-6">Privacy Policy</h1>
      <p className="text-silver text-sm mb-8">Last updated: March 13, 2026</p>

      <div className="space-y-6 text-slate text-sm leading-relaxed">
        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Overview</h2>
          <p>
            Mirth is a multiplayer party game app. We are committed to protecting your privacy.
            This policy explains what data we collect, how we use it, and your rights.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Data We Collect</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Google Sign-In:</strong> If you sign in with Google, we receive your display name, email address, and profile picture from Google. We do not receive or store your Google password.</li>
            <li><strong>Guest Players:</strong> If you play as a guest, we only store the display name you choose. No personal information is collected.</li>
            <li><strong>Game Data:</strong> We store game scores, room participation, and chat messages sent during gameplay to provide the game experience.</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">How We Use Your Data</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>To identify you in game rooms and display your name and avatar to other players</li>
            <li>To maintain game scores and history</li>
            <li>To enable real-time multiplayer gameplay</li>
          </ul>
          <p className="mt-2">We do not sell, share, or transfer your personal data to any third parties.</p>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Data Storage</h2>
          <p>
            Your data is stored on our servers and retained for as long as your account exists.
            Game chat messages and room data may be deleted periodically as rooms are closed.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Third-Party Services</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Google Sign-In:</strong> Used for authentication. Subject to Google's Privacy Policy.</li>
          </ul>
          <p className="mt-2">We do not use analytics, advertising, or tracking services.</p>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Your Rights</h2>
          <p>You can:</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Play as a guest without providing any personal information</li>
            <li>Request deletion of your account and associated data</li>
          </ul>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Children's Privacy</h2>
          <p>
            Mirth is not directed at children under 13. We do not knowingly collect
            personal information from children under 13.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-ink text-base mb-2">Contact</h2>
          <p>
            If you have questions about this privacy policy or want to request data deletion,
            contact us at <a href="mailto:sumit.skdev018@gmail.com" className="text-accent underline">sumit.skdev018@gmail.com</a>.
          </p>
        </section>
      </div>
    </div>
  )
}
