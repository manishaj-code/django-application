# Administrator Guide

This guide is for the people who run the website day to day. You don't need
any programming knowledge.

The admin panel is at **`https://<your-domain>/admin/`**. Your technical
contact may have moved it to a different address via the `ADMIN_URL`
setting. Once signed in on the public site, you can also open it from your
name menu → **Admin panel**.

---

## 1. Signing in

1. Go to the admin address.
2. Enter your **username** and **password** and click **Log in**.
3. Only accounts with **Staff status** can sign in here. Ordinary members
   who registered on the site cannot.
4. After several wrong passwords in a minute you'll see "Too many attempts".
   Wait a minute and try again.

To sign out, click **Log out** at the top right.

## 2. Roles at a glance

| Role | How it's set up | Can do |
|---|---|---|
| Member | Registers on the public site | Manage their own profile and password |
| Editor | *Staff status* + member of the **Editors** group | Create, edit, publish and delete content and categories; read contact messages |
| Administrator | *Superuser status* | Everything, including users and permissions |

Give people the **least** access they need. Most staff only need to be Editors.

---

## 3. Creating content

1. Click **Content → Content → Add content item**.
2. Fill in:
   - **Title** (required).
   - **Slug**: the web address, e.g. `/content/my-first-article/`. It fills
     in automatically as you type the title. It must be unique. Avoid
     changing it after publishing, because old links will stop working.
   - **Category** (optional).
   - **Summary**: one or two sentences shown on listing cards.
   - **Body** (required): plain text. Leave a **blank line** between
     paragraphs. HTML tags are shown as text, not interpreted.
   - **Featured image** (optional): JPG, PNG, WebP or GIF, up to 5 MB by
     default.
3. Under **Publication**, leave **Status = Draft** to keep working on it
   privately, or choose **Published**.
4. Click **Save**, **Save and continue editing**, or **Save and add another**.

**Preview a draft:** open the item and click the **Preview (not public yet)**
link in the *Publication* section. Only signed-in staff can see drafts. The
public gets "Page not found".

## 4. Editing and deleting content

- **Edit:** click the item's title in the list, change it, then **Save**.
- **Delete one:** open it → **Delete** (bottom left) → confirm.
- **Delete several:** tick them in the list → *Action:* **Delete selected
  content** → **Go** → confirm.

Deleting is permanent and also removes the item's image file. If you might
want it back later, unpublish it instead.

## 5. Publishing, unpublishing and scheduling

- **Publish:** set *Status* to **Published** and save. *Published at* is
  filled in with the current time if empty.
- **Publish many at once:** tick items → *Action:* **Publish selected items** → **Go**.
- **Unpublish:** set *Status* back to **Draft**, or use the action
  **Unpublish selected items (back to draft)**. The item disappears from
  the public site immediately.
- **Schedule:** set *Status* to **Published** and *Published at* to a future
  date and time. The item appears automatically at that time.
- If you republish an item, it keeps its original publication date. To
  bring it to the top of the list, change *Published at* to now (click
  **Today** / **Now**).

## 6. Finding content

- **Search box:** searches titles, slugs, summaries and body text.
- **Filters** (right side): by status, category, publication date and
  creation date.
- **Date links** above the list let you drill down by year, month and day.
- Click a column heading to sort.

## 7. Managing categories

**Content → Categories.**

- **Add:** enter a *Name*. The *Slug* fills in automatically. The
  description is optional and appears on the category page.
- **Rename:** edit the name. Keep the slug unless you know you want the web
  address to change.
- **Delete:** content in that category is **not** deleted. It just becomes
  "uncategorised".
- The *Items* column shows how many content items use each category.

## 8. Contact messages

**Site → Contact messages** lists everything sent through the public contact
form. Open a message to read it, and tick **Read** (or use the *Mark selected
messages as read* action) to keep track. Messages can't be created or edited
here, only read, marked or deleted.

If your technical contact has set `CONTACT_RECIPIENT_EMAIL`, a copy of each
message is also emailed to that address.

---

## 9. Managing users and permissions (administrators only)

**Accounts → Users.**

- **Create a user:** **Add user** → username, email, password (twice) →
  **Save**. You then reach the full edit page.
- **Make someone an editor:**
  1. Open the user.
  2. Under *Permissions*, tick **Staff status**.
  3. In *Groups*, move **Editors** to *Chosen groups*.
  4. **Save**.
- **Make someone a full administrator:** tick **Superuser status**. Grant
  this sparingly.
- **Remove access:** untick **Staff status** to remove admin access, or
  untick **Active** to block sign-in completely. Unticking *Active* is better
  than deleting, because it keeps their history.
- **Groups:** **Authentication and Authorization → Groups → Editors** shows
  what editors may do. You can add or remove permissions there. Changes
  apply to every member of the group.

Ordinary users can never give themselves staff or admin rights. Only an
administrator can, here.

## 10. Resetting passwords

- **A user forgot their password:** they can click **Forgot your password?**
  on the sign-in page and follow the emailed link, which works once and
  expires after 24 hours.
- **Set a password for someone:** open the user → under *Password*, click
  **Reset password** → enter the new password twice → **Change password**.
  Tell them to change it after signing in (*name menu → Change password*).
- **Change your own password:** top right of the admin → **Change password**.
- **All administrators are locked out:** your technical contact can run
  `python manage.py changepassword <username>` or
  `python manage.py createsuperuser` on the server.

---

## 11. Troubleshooting

| What you see | What to do |
|---|---|
| "Please enter the correct username and password for a staff account" | Check spelling and caps lock. The account also needs *Staff status* and *Active* ticked. |
| "Too many attempts" | Wait a minute (sign-in) or an hour (password reset), then retry. |
| "Content item with this Slug already exists" | Choose a different slug, or clear the field to generate one. |
| Image upload rejected | Use JPG/PNG/WebP/GIF under the size limit (5 MB by default), and make sure the file really is an image. |
| Item doesn't appear on the site | Check that *Status* is **Published** and *Published at* isn't in the future. |
| "403 Forbidden" in admin | Your account lacks permission for that section. Ask an administrator to add you to the right group. |
| "Session expired" / 403 on a form | The page was open too long. Reload and try again. |
| Password reset email never arrives | Check spam. Make sure the email address on the account is correct. Then ask your technical contact to check the email settings. |
