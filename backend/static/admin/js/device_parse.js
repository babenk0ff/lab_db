'use strict';

const modal = document.querySelector('.modal');
const parseFormLink = JSON.parse(document.getElementById('url_parse').text);
const saveFormLink = JSON.parse(document.getElementById('url_parsed_save').text);

window.addEventListener('load', async (event) => {
    const modalContent = document.querySelector('.modal-content');
    const parseFormMarkup = await getParseFormMarkup(parseFormLink);

    // Вставка формы парсинга
    modalContent.insertAdjacentHTML('beforeend', parseFormMarkup);

    // Добавление кнопки показа модального окна
    document.querySelector('.object-tools')
        .insertAdjacentHTML(
            'afterbegin',
            `<li><a href="#" class="addlink modal_show">Добавить из строки</a></li>`
        );

    // Событие показа модального окна
    document.querySelector('.modal_show')
        .addEventListener('click', (event) => {
            modal.style.display = 'block';
        });

    // Событие скрытия модального окна
    document.querySelector('.modal_hide')
        .addEventListener('click', (event) => {
            modal.style.display = 'none';
        });

    // Отслеживание событий отправки формы из модального окна
    modalContent.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (event.target.id === 'form-parse') {
            const formData = new FormData(event.target);
            const formMarkup = await getParseFormMarkup(parseFormLink, formData);
            replaceForm(formMarkup);
        } else if (event.target.id === 'form-parse-save') {
            const formData = new FormData(event.target);
            const formMarkup = await getParseFormMarkup(saveFormLink, formData);
            replaceForm(formMarkup);

            const redirect = document.getElementById('redirect_url');
            if (redirect) {
                const redirectUrl = JSON.parse(redirect.text);
                window.location.replace(redirectUrl);
            }
        }
    });

    // Событие очистки формы
    modalContent.addEventListener('click', async event => {
        if (event.target.id === 'parse-reset') {
            event.preventDefault();
            const formMarkup = await getParseFormMarkup(parseFormLink);
            replaceForm(formMarkup);
        }
    })
});

/**
 * Отправляет на сервер данные из формы парсинга и получает в ответ
 * HTML-разметку обновленной формы.
 * @param url Эндпоинт для отправки данных формы
 * @param formData Данные из формы
 * @returns {Promise<string>} HTML-разметка обновленной формы
 */
async function getParseFormMarkup(url, formData = undefined) {
    if (formData) {
        const response = await fetch(url, {
            body: formData,
            method: 'post',
        });
        return await response.text();
    }
    const response = await fetch(url);
    return await response.text();
}

/**
 * Заменяет текущую форму на новую
 * @param formMarkup HTML-раметка новой формы
 */
function replaceForm(formMarkup) {
    document.querySelector('.parse-form_wrapper').remove();
    document.querySelector('.modal-content')
        .insertAdjacentHTML("beforeend", formMarkup);
}
