import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
test('switching accounts clears documents and selects the authorized unit',async({page})=>{
 test.skip(!process.env.KARMA_E2E_CREDENTIALS,'Requires disposable scoped users');
 const fixture=JSON.parse(readFileSync(process.env.KARMA_E2E_CREDENTIALS!,'utf8'));
 async function login(username:string,password:string){await page.getByRole('button',{name:/ورود به فضای کارکنان/}).click();await page.getByLabel('نام کاربری').fill(username);await page.getByLabel('رمز عبور',{exact:true}).fill(password);await page.getByRole('button',{name:'ورود امن'}).click();await expect(page.locator('.profile')).toContainText(username)}
 await page.goto('/');await login(fixture.username,fixture.password);
 await page.getByRole('button',{name:'فروش و خرید'}).click();await expect(page.locator('tbody tr').first()).toBeVisible();
 await page.getByRole('button',{name:'خروج',exact:true}).click();
 await login(fixture.second_username,fixture.second_password);
 await page.getByRole('button',{name:'فروش و خرید'}).click();
 await expect(page.getByRole('combobox',{name:'واحد تجاری'})).toHaveValue(String(fixture.second_unit));
 await expect(page.getByText('هنوز رکوردی ثبت نشده است.')).toBeVisible();
 await expect(page.locator('tbody tr')).toHaveCount(0);
});
